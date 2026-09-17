Dataset 构建与 Eval 框架搭建
===

评测对象：本地 Agent 记忆系统 ReMe（当前以 BM25 baseline 接入）与本地 LLM
任务：构建 8 维 Agent Memory 评测数据集 MemEval-v0.1，并搭建 Dataset→Memory→Answer LLM→Judge LLM→Trace→Dashboard 端到端评测框架
交接节点：MemEval-v0.1（298 条冻结 case，D01–D08）已完成发布并冻结；

---

一、任务启动与 7 套公开数据源收集
---

**背景与设计原则**

Agent 记忆评测要覆盖记忆系统的多维度能力，不能只靠单一 benchmark。v0.1 不追求大量 Case，目标是先把 8 个维度的数据构建 + 系统运行 + 指标计算完整跑通。

总体设计为三层数据转换 + 两层运行转换：

```text
公开原始数据
↓ Source Adapter
Canonical Source Record
↓ Dimension Builder
Benchmark Case
↓ System Adapter
Memory System
↓ Evaluator
```

**维度与数据源锁定**（8 维 8 源）：

| ID | 测试维度 | 主数据集 |
| --- | --- | --- |
| D01 | 记忆抽取与写入 | LongMemEval |
| D02 | 基础长期记忆 | LongMemEval |
| D03 | 长时间跨度对话 | LoCoMo |
| D04 | 主动调用与记忆使用 | PrefEval |
| D05 | 用户画像与偏好 | PersonaMem-v2 |
| D06 | 动态更新与冲突 | MemoryAgentBench |
| D07 | 超大规模长上下文 | BEAM |
| D08 | 隐私与用户隔离 | AgentMemBench |

**版本固定（Manifest）**

- LongMemEval 用官方推荐 cleaned 版 `xiaowu0162/longmemeval-cleaned`（`longmemeval_oracle.json` + `longmemeval_s_cleaned.json`），不用 deprecated 旧版，暂不切 LongMemEval-V2。
- LoCoMo 固定官方 `data/locomo10.json`，不用第三方重格式化版本。
- PrefEval 官方拆三套 HF Dataset（explicit / implicit_choice / implicit_persona，各 1000 条）全部下载。
- PersonaMem-v2 只用 text + 32K chat history，不用 128K 与 multimodal（规模变量统一交给 D07）。
- MemoryAgentBench 只下载 Conflict_Resolution（2025-09-29 后更新版，含修复 qa_pair_ids）。
- BEAM 固定普通版 100K/500K/1M + BEAM-10M，probing_questions 用 `ast.literal_eval` 安全解析，不 `eval`。
- AgentMemBench 用官方 release-verified 的 MemDialogue v2（9170 个 memory event，带 meta 与 deterministic audit）。

每套源在 `manifests/*.yaml` 固定 dataset_name / source_repo / source_revision(commit SHA 或 HF revision) / download_date / license / files / file_hashes / adapter_version。

---

二、数据架构设计（Common Envelope / Canonical Event / context_ref）
---

**统一的是 Envelope，不是 Gold**

不建议把 8 个维度的 Gold 强行统一，每个 Dimension 自己维护 `gold.payload_type + payload`。统一 Case 推荐结构使用 `schema_version / envelope(source, identity, context, query, metadata) / gold`；`user_id / tenant_id / timestamp` 允许为空但字段固定存在。

**为什么用 context_ref 而不是把完整 Context 复制进每个 Case**

LongMemEval、BEAM、MemoryAgentBench 都有多个 Question 共用一个 Context。若 Case 内复制，BEAM-10M Context × 几十个 Question 会产生大量重复数据。因此维度目录拆成 `contexts/` 与 `cases/`，Case 只保留 `context_ref`，Runner 运行时加载 Context（支持 `reuse_context`，一次 ingest 多次 query 与逐个 case 独立两种模式分开记录）。

**Canonical Event Schema**

所有 Source Adapter 尽量映射到统一事件：

```text
event_id / session_id / turn_id / order / timestamp / role / content / source_ref / metadata
```

LoCoMo `dia_id`→turn_id/source_ref；LongMemEval 与 BEAM chat turn→role/content；MemoryAgentBench document chunk→role: document。不为凑 user/assistant 格式伪造 conversation role。

---

三、Source Adapter：迁移三个，新写四个
---

统一接口

```text
load_raw() / audit() / normalize() / validate() / iter_records()
```

**已有三个 Adapter 的迁移策略**（能改不重写，能包 Wrapper 不动内部，先保旧测试过，再加 `test_legacy_equivalence` 防迁移破坏）：

- LongMemEval：先建 fixture → 升级 cleaned 路径 → 挂 SourceAdapter Interface → 输出 Canonical Event → 加 source metadata。
- LoCoMo：建 fixture → 保留 Session 与 Timestamp → 核查 category 映射（JSON 编号与论文顺序不一致，必须以官方 evaluation code + 本地数据联合核验，不按论文段落硬编码）→ 输出 Canonical Event。
- PersonaMem-v2：建 fixture → 锁定 text+32K → 建 persona_id 到 raw_data/history 索引 → 加 profile source metadata。

**新写四个的优先级**（开发文档建议顺序）：PrefEval（结构小最易，验证新接口）→ MemoryAgentBench（验证一 Context 多 Query）→ AgentMemBench（验证事件/多用户/删除/隐私）→ BEAM（多 Scale + 超长 + 10M 特殊结构 + probing 字符串解析，复杂度最高，不拿它做首套实现）。

关键结构：MemoryAgentBench Conflict Resolution 顶层只有 8 条 record，每条 record 内含 `context + questions[] + answers[][] + metadata(previous_events/keypoints/question_dates/qtype...)`，不是 8 个样本，需 Builder 展开成 37 个独立 Case；不能假定 BEAM-10M 与普通版 100K/500K/1M 同构。

产物输出到 staging 目录（`d01_write/… / d08_privacy/`，各含 contexts/ + records.jsonl），可追溯、结构统一、保留原始 Source ID 与全部 Gold Candidate，但还不是最终 Benchmark。

---

四、Dimension Builder 与八套 Gold Payload
---

统一接口：

```text
load_candidates() / filter_candidates() / derive_gold() / sample_cases() / validate_cases() / build()
```

Builder 承载真正 Benchmark 逻辑（D04 决定 should_activate，D08 决定跨用户组合等）。各维 Gold 与指标口径：

| 维度 | payload_type | Gold 关键字段 | 指标 |
| --- | --- | --- | --- |
| D01 | write | scored_event_ids、gold_memories(memory_id/canonical_content/type/evidence_event_ids)、non_memory_event_ids | Write Precision / Recall |
| D02 | retrieval | gold_evidence_ids、gold_answer、retrieval_k=[1,3,5,10] | Hit@K / Recall@K / MRR |
| D03 | temporal | gold_answer、evidence_event_ids、time_gap_days、lifecycle(valid_from/until/deleted_at/expected_active) | Temporal Accuracy / Long-gap Recall / Deleted Hit Rate |
| D04 | activation | should_activate、required_memory_ids、preference、answer_criteria | Activation Precision / Recall / Utilization / E2E Accuracy |
| D05 | profile | profile_items(slot/value/evidence)、target_preference_ids | Profile Precision / Preference Recall / Profile Consistency |
| D06 | conflict | fact_versions、winning_fact_ids、stale_fact_ids | Latest-value / Conflict Resolution Acc / Stale Retrieval Rate |
| D07 | scale | scale_group_id、scale_level、paired_anchor_id、expected_retrievable | Recall by Scale / Recall Degradation / Latency / Cost |
| D08 | privacy | scenario_type、owner/querying_user_id、allowed/forbidden/deleted_memory_ids、canary_tokens | Leakage Rate / Deletion Completeness / Canary Exposure Rate |

**几条关键构造约定**

- D01：LongMemEval 的 Evidence 只证明哪些内容能答某 Question，不能直接等价为"应该写入的 Memory"，故 D01 必须加人工 Gold Memory Annotation，采用有限 Scoring Window（Evidence Session + 邻近 Distractor + 少量普通 Session）后人工标注（9/1 已完成 D01 38 case 人工核验）。
- D02：直接用 LongMemEval 自带 Gold Evidence，不重复标答案；排除 `_abs` 拒答变体；Context 移除 `has_answer` 及所有 Gold 标签元数据，避免答案泄漏。
- D04：必须同时有 Activation Positive（implicit_choice/implicit_persona 抽取）与 Negative（explicit 构建），否则识别不出系统"无条件调用 Memory"。
- D05：选 `updated=false / sensitive_info=false / who=user`、persona_id 不重复，将 D05 与 D06 动态更新能力解耦。
- D06：检查 questions/answers/qa_pair_ids/question_types 严格一一对应，从 8 个 Context 展开 37 Case，尽量 half single-hop / half multi-hop。
- D07：真正的 Recall Degradation 必须来自同一 conversation 的 Paired Scale Case（Gold Evidence/Question/Answer 不变、只变 Context Size），不能拿不同 BEAM conversation 的 100K 与 10M 直接比；本地若无法可靠定位 Evidence，不强行生成 paired、不能为凑指标伪造 Evidence。
- D08：Canary 用人工生成、无现实意义、全局唯一的 Token（如 `PRIVATE_CANARY_A_0042`），用泄漏检测而非真实敏感数据；Deletion 需验证"删除前确实存在"。

---

五、Case 冻结与 Benchmark Audit
---

**采样冻结**

所有 300 Case 抽取固定 `selection_seed = 20260901`，把最终选中的 `source_record_id / source_question_id` 写入 manifest，使 v0.1 可完全复现。用 `scripts/freeze_memeval_selection.py` 冻结（09-08 stage 31），保证消融各 arm case 一致。

**最终发布规模（MemEval-v0.1，298 条）**

| 维度 | Case 数 |
|---|---:|
| D01 记忆抽取与写入 | 37 |
| D02 长期记忆检索 | 37 |
| D03 长时间跨度对话 | 38 |
| D04 主动记忆激活 | 38 |
| D05 用户画像与偏好 | 37 |
| D06 动态更新与冲突 | 37 |
| D07 超长上下文 | 37 |
| D08 隐私与用户隔离 | 37 |
| 合计 | 298 |

**完整性核验（阶段 23 audit.py 直接核验正式目录）**

- 全局重复 case_id / query_id = 0，缺失 Context 引用 = 0，Source Audit 7/7 通过，最终完整性核验 PASS。
- 无 Source Gold 泄漏进入 Query、无 Answer 泄漏进入 Context Metadata，Evidence ID 全部可解析。
- D04 Positive/Negative = 19/19；D07 同 scale_group 的 Query/Answer/Gold Evidence 一致且 Scale 单调增加；D08 owner≠querying、forbidden/deleted 存在、Canary 唯一。

---

六、Eval 框架搭建
---

**四层 Adapter 架构**

Runner 只组织流程、不理解具体实现，`Dataset → Memory → Answer LLM → Judge LLM → Trace` 之间以四类 Adapter 解耦（`memory_eval/adapters/`）：

| 层 | 角色 | 当前实现 | 是否实验变量 |
| --- | --- | --- | --- |
| dataset | 读 benchmark 转统一 case | longmemeval / locomo / personamem-v2（auto 识别） | 是 |
| memory | 单 case 隔离/写入/索引/检索/清理 | reme（真实）/ off（无记忆对照） | 是 |
| llm | 请求/错误归类/重试/usage 透传 | openai-compatible（Answer 与 Judge 独立配置，可连 vLLM） | 是 |
| Trace | 汇总产物→报告/Dashboard | memeval（与八维绑定） | 否（框架配套） |

统一 case 结构：`case_id / question / gold_answer / question_type / question_date / sessions[](session_id, timestamp, messages[]) / evidence_session_ids[]`，使同一 Memory Adapter 无差别消费不同 benchmark。`memory_eval/systems/` 再加一层 System Adapter，声明能力边界（capabilities：retrieval/profile/delete/user_isolation…）并包住 Memory Adapter；系统不支持某能力时 Evaluator 返回 `unsupported`，不自动记 0 分（否则在评 API 而不是 Memory 能力）。

新增实现只新增实现文件 + 在 registry 登记，Runner 不该加实现专用分支。API 密钥只在被 `.gitignore` 忽略的 `.env`，不写进代码或 report。

**端到端编排与消融对照**

入口 `scripts/run_memeval.py`，一键跑 `Retrieval → Answer → Judge → Trace → Dashboard`；Retrieval 成功才进 Answer，Answer 成功才进 Judge，失败 case 与成功输出对账后按 case_id 续跑。`--memory-adapter off` 为无记忆消融对照（走完整流程，检索指标如实记 0，用于衡量 memory 净增益）；`retrieval_run_config.json` 记录 run 完整配置，resume 时校验防止混跑，并带 `eval_code_snapshot/`（源码 + SHA-256 manifest）保证复现。

**指标口径演进（关键修正）**

- 早期全量完整 session 作为单个 chunk（10000-byte）导致 D02 Session Recall 虚高（达 90.6%）；改为 1500-byte 小 chunk 检索。
- 早期按 session 去重 top-K 检索块，丢弃了约 90% 同 session 含证据块，显著拉低 needle recall；改为保留全部 top-K 不按 session 去重。
- D02 与 D05 口径对调：D02 保持 **session 级** Hit@K/Recall@K/MRR（primary K=3）+ answer_accuracy（`primary=None`，不设单一主指标）；D05 改为 **needle 级纯检索召回**（Recall/Hit/MRR，K=1/3/5/10 全档位，含 evidence count 字段），Answer/Judge 走 `NOT_APPLICABLE`，不再进答案/评审阶段。
- D01/D07/D08 修正为反映真实能力，而不是 trivial 分数。

**Dashboard（静态 HTML，无需服务器）**

`memory_eval/html_report.py` 产出 `Trace Summary/Dashboard.html`。已移除引起误导的首页 CORE METRICS 聚合段（避免跨维度聚合误读）；保持 8 维展示不变，不支持的能力标"不支持"而非替换成别的指标；D05 needle 级卡片配 session 级参考，避免 K 指标混到 needle 卡片造成高值误判。展示逻辑升级后旧 run 可用 `--trace-only --run-dir …` 从已持久化产物重建报告，不重跑、不调 LLM。Dashboard 基线固定为 `dashboard-baseline-v1`（commit 34d305d）。

运行结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离（reme / off 各自成目录），`Detailed Trace Report/` 存原始产物与溯源，`Trace Summary/` 存面向人的 Dashboard 与精简摘要。

---

七、关键文件存放位置
---

**数据源与 Dataset 构建**

| 路径 | 内容 |
|---|---|
| dataset/MemEval-v0.1/ | 冻结评测数据集（298 case，D01–D08） |
| dataset/MemEval-v0.1/manifests/*.yaml | 7 套源的版本/哈希固定 |
| dataset/MemEval-v0.1/dimensions/*/v0.1/ | 各维度 contexts/ cases/ + 评测口径 README |
| dataset/MemEval-v0.1/Agent Memory Eval 数据集构建开发文档 v0.1.md | 数据集构建规范 |
| dataset/build_pipeline/sources/ | Source Adapter（longmemeval/locomo/prefeval/personamem_v2/memoryagentbench/beam/agentmembench） |
| dataset/build_pipeline/dimensions/ | Dimension Builder（d01_write…d08_privacy） |
| dataset/build_pipeline/{staging,release,selection,audit}.py | staging 生成 / release 发布 / 采样冻结 / 完整性核验 |

**Eval 框架**

| 路径 | 内容 |
|---|---|
| scripts/run_memeval.py | 端到端编排入口 |
| memory_eval/runners/memeval.py、context_cache.py | Runner 与 Context 缓存 |
| memory_eval/adapters/{dataset,memory,llm,Trace}/ | 四层 Adapter + registry |
| memory_eval/systems/{reme,off}.py | System Adapter（含 NoMemory 消融对照） |
| memory_eval/{trace_report,html_report,result_layout}.py | Trace / Dashboard / 结果布局 |
| scripts/freeze_memeval_selection.py | case 选择冻结 |
| README.md / USAGE_ZH.md | 使用手册 |
| docs/ | 设计与评审文档（MemoryEval_CheckList / memory_eval_html / requirements） |

**指标口径落点**

D02 检索 chunk 大小、top-K 保留（不按 session 去重）、session/needle 指标分桶等口径调整，全部落在 `memory_eval/metrics/` 与 runner/html_report 层，数据层（dataset/）保持稳定，无需改动即可复现。

---