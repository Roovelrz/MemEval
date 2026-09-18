Dataset 构建与 Eval 框架搭建
===

任务：构建 8 维 Agent Memory 评测数据集 MemEval-v0.1，并搭建
`Dataset→Memory→Answer→Judge→Trace→Dashboard` 端到端评测框架。对象：本地记忆系统 ReMe
（当前 BM25 baseline）与本地 LLM。交接节点：MemEval-v0.1（298 条冻结 case）已发布并冻结。

---

## 一、7 套公开数据源收集

**设计**：不靠单一 benchmark，覆盖记忆系统多维度能力；v0.1 以跑通"数据构建 + 系统运行 +
指标计算"为要，不追量大。三层数据转换 + 两层运行转换：

```text
公开原始数据 → Source Adapter → Canonical Source Record → Dimension Builder →
Benchmark Case → System Adapter → Memory System → Evaluator
```

**8 维 8 源**：

| ID | 维度 | 主数据集 |
| --- | --- | --- |
| D01 | 记忆抽取与写入 | LongMemEval |
| D02 | 基础长期记忆 | LongMemEval |
| D03 | 长时间跨度对话 | LoCoMo |
| D04 | 主动调用与记忆使用 | PrefEval |
| D05 | 用户画像与偏好 | PersonaMem-v2 |
| D06 | 动态更新与冲突 | MemoryAgentBench |
| D07 | 超大规模长上下文 | BEAM |
| D08 | 隐私与用户隔离 | AgentMemBench |

**版本固定要点**：LongMemEval 用官方 cleaned（`longmemeval_oracle.json` + `longmemeval_s_cleaned.json`），
暂不切 V2；LoCoMo 固定官方 `locomo10.json`；PrefEval 三套 HF Dataset 全下；PersonaMem-v2 只用
text + 32K（规模并给 D07）；MemoryAgentBench 只用更新版 Conflict_Resolution；BEAM 固定普通版
100K/500K/1M + BEAM-10M，probing 用 `ast.literal_eval` 不 `eval`；AgentMemBench 用
release-verified 的 MemDialogue v2。每套源在 `manifests/*.yaml` 固定
dataset_name/source_repo/revision/date/license/files/hashes/adapter_version。

---

## 二、数据架构设计

**统一的是 Envelope，不是 Gold**：8 维 Gold 不必统一，每维自维护
`gold.payload_type + payload`；Case 用 `schema_version/envelope(source, identity, context, query,
metadata)/gold`。`user_id/tenant_id/timestamp` 允许空但字段固定存在。

**用 context_ref 而非复制 Context**：多 Question 共用一个 Context 时（LongMemEval/BEAM/
MemoryAgentBench），Case 内复制会造成 BEAM-10M×几十 Question 的巨量重复。维度目录拆
`contexts/` 与 `cases/`，Case 只保留 `context_ref`，Runner 运行时加载（支持 `reuse_context`：
一次 ingest 多次 query 与逐 case 独立两种模式分开记录）。

**Canonical Event**：`event_id/session_id/turn_id/order/timestamp/role/content/source_ref/metadata`。
LoCoMo `dia_id`→turn_id/source_ref；MemoryAgentBench document chunk→`role: document`；
不为凑 user/assistant 伪造 role。

---

## 三、Source Adapter：迁移三个，新写四个

统一接口 `load_raw()/audit()/normalize()/validate()/iter_records()`。已有三个 Adapter"能改不重写、
能包 Wrapper 不动内部、先保旧测试过、再加 `test_legacy_equivalence`"。要点：LoCoMo `category`
映射必须按官方 evaluation code + 本地数据联合核验，不按论文顺序硬编码；PersonaMem-v2 锁定
text+32K、建 persona_id→history 索引。新写四个优先级：PrefEval（最易，验证新接口）→
MemoryAgentBench（验证一 Context 多 Query）→ AgentMemBench（事件/多用户/删除/隐私）→ BEAM
（多 Scale+超长+10M 特殊结构+probing 解析，复杂度最高，不做首套）。关键：MemoryAgentBench
Conflict Resolution 顶层仅 8 条 record，每条内含 context+questions+answers+metadata，需 Builder
展开成 37 个 Case；BEAM-10M 与普通版不同构。产物输出到 `staging/*/`（contexts/ + records.jsonl），
可追溯但还不是最终 Benchmark。

---

## 四、Dimension Builder 与八套 Gold

统一接口 `load_candidates()/filter_candidates()/derive_gold()/sample_cases()/validate_cases()/build()`。
Builder 承载真正 Benchmark 逻辑（D04 定 should_activate、D08 定跨用户组合等）。各维 Gold 与指标：

| 维度 | payload_type | Gold 关键字段 | 指标 |
| --- | --- | --- | --- |
| D01 | write | scored_event_ids、gold_memories(memory_id/canonical_content/type/evidence_event_ids)、non_memory_event_ids | Write Precision/Recall |
| D02 | retrieval | gold_evidence_ids、gold_answer、retrieval_k=[1,3,5,10] | Hit@K/Recall@K/MRR |
| D03 | temporal | gold_answer、evidence_event_ids、time_gap_days、lifecycle | Temporal Acc/Long-gap Recall/Deleted Hit |
| D04 | activation | should_activate、required_memory_ids、preference、answer_criteria | Activation P/R/Utilization/E2E Acc |
| D05 | profile | profile_items(slot/value/evidence)、target_preference_ids | Profile P/Preference Recall/Consistency |
| D06 | conflict | fact_versions、winning_fact_ids、stale_fact_ids | Latest-value/Conflict-Res Acc/Stale Retrieval |
| D07 | scale | scale_group_id、scale_level、paired_anchor_id、expected_retrievable | Recall@Scale/Degradation/Latency/Cost |
| D08 | privacy | scenario_type、owner/querying_user_id、allowed/forbidden/deleted_memory_ids、canary_tokens | Leakage/Deletion Completeness/Canary Exposure |

**关键构造约定**：D01 的 LongMemEval Evidence 只证明"能答某题"，不等价"应写入 Memory"，需人工
Gold Annotation（有限 Scoring Window：证据 session + 邻近 distractor + 少量普通 session）；D02
直接用自带 Gold Evidence、排除 `_abs` 拒答变体、Context 移除 `has_answer` 防泄漏；D04 必须
Positive/Negative 兼有；D05 选 `updated=false/sensitive_info=false/who=user` 且 persona_id 不重复，
与 D06 解耦；D06 校验 questions/answers/qa_pair_ids/question_types 严格一一对应、half
single-hop/half multi-hop；D07 真正的 Recall Degradation 必须来自同 conversation 的 Paired Scale
Case（Evidence/Question/Answer 不变、只变 Context Size），不能拿不同 conversation 的 100K vs
10M 比，也不能凑指标伪造 Evidence；D08 用人工全局唯一 Canary Token（如 `PRIVATE_CANARY_A_0042`）
做泄漏检测，Deletion 需验证"删除前确实存在"。

---

## 五、Case 冻结与 Audit

所有 Case 固定 `selection_seed=20260901`，把选中的 `source_record_id/source_question_id` 写入
manifest，用 `scripts/freeze_memeval_selection.py` 冻结，可完全复现。

**最终规模（MemEval-v0.1，298 条）**：D01/02/05/06/07/08 各 37，D03/04 各 38。

**完整性核验**：case_id/query_id 全局无重复、缺失 Context ref=0、Source Audit 7/7 通过；无 Gold
泄漏进 Query、无 Answer 泄漏进 Context Metadata、Evidence ID 全可解析；D04 Positive/Negative=19/19；
D07 同 scale_group 的 Query/Answer/Gold 一致且 Scale 单调增；D08 owner≠querying、forbidden/deleted
存在、Canary 唯一。

---

## 六、Eval 框架搭建

**四层 Adapter**：Runner 只组织流程不解具体实现，`Dataset→Memory→Answer→Judge→Trace` 以四类
Adapter 解耦（dataset/memory/llm/Trace）。dataset/llm/memory 是实验变量可替换，Trace 与八维绑定、
框架配套。统一 case 结构让同一 Memory Adapter 无差别消费不同 benchmark。`memory_eval/systems/`
再加 System Adapter 声明能力边界（capabilities: retrieval/profile/delete/user_isolation…）；
系统不支持某能力时返回 `unsupported` 不自动记 0（否则评的是 API 而不是 Memory 能力）。新增实现
只加文件 + 登记 registry，Runner 不加专用分支；API 密钥只在 `.gitignore` 忽略的 `.env`。

**端到端与消融**：入口 `scripts/run_memeval.py`，一键跑 Retrieval→Answer→Judge→Trace→Dashboard；
上游成功才进下游，失败按 case_id 续跑。`--memory-adapter off` 为无记忆对照（检索指标如实记 0）；
`retrieval_run_config.json` 记录配置、resume 时校验防混跑；`eval_code_snapshot/` 保存源码 +
SHA-256 manifest 保证复现。

**指标口径演进（关键修正）**：

- 早期全量 session 作单 chunk（10000-byte）致 D02 Session Recall 虚高（达 90.6%）→ 改 1500-byte 小 chunk。
- 早期按 session 去重 top-K 检索块，丢掉约 90% 同 session 含证据块 → 改为保留全部 top-K 不去重。
- D02/D05 口径对调：D02 保持 **session 级** Hit@K/Recall@K/MRR（primary K=3）+ answer_accuracy
  （`primary=None`）；D05 改为 **needle 级纯检索召回**（Recall/Hit/MRR，K=1/3/5/10 全档位，
  含 evidence count），Answer/Judge 走 `NOT_APPLICABLE`，不进答案/评审。
- D01/D07/D08 修正为反映真实能力，而非 trivial 分数。

**Dashboard**：`memory_eval/html_report.py` 产出静态 HTML。已移除首页 CORE METRICS 聚合段（避免
跨维度聚合误读）；保持 8 维展示不变，不支持的能力标"不支持"而非替换；D05 needle 级卡片配
session 级参考避免高值误判。展示升级后旧 run 用 `--trace-only --run-dir …` 重建报告、不重跑。
基线固定 `dashboard-baseline-v1`（commit 34d305d）。结果按 `results/memeval_v0_1/<system>/<run-id>/`
隔离，`Detailed Trace Report/` 存原始产物溯源，`Trace Summary/` 存 Dashboard 与摘要。

---

## 七、关键文件存放位置

**数据 / 构建**：`dataset/MemEval-v0.1/`（冻结 298 case）；`.../manifests/*.yaml`（源版本固定）；
`.../dimensions/*/v0.1/`（各维 contexts/cases + 口径 README）；`.../Agent Memory Eval…v0.1.md`
（构建规范）；`dataset/build_pipeline/{sources,dimensions}.py`（Adapter/Builder）；
`{staging,release,selection,audit}.py`（构建/发布/冻结/核验）。

**Eval 框架**：`scripts/run_memeval.py`（入口）；`memory_eval/runners/memeval.py`、`context_cache.py`；
`memory_eval/adapters/{dataset,memory,llm,Trace}/`；`memory_eval/systems/{reme,off}.py`；
`memory_eval/{trace_report,html_report,result_layout}.py`；`scripts/freeze_memeval_selection.py`。
`README.md / USAGE_ZH.md` 使用手册。

**指标口径落点**：D02 chunk 大小、top-K 不去重、session/needle 分桶等口径全在
`memory_eval/metrics/` 与 runner/html_report 层；数据层（dataset/）稳定，无需改动即可复现。