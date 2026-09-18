# Agent Memory Eval 数据集构建开发文档 v0.1

## 1. 目标与范围

构建覆盖 8 个记忆能力维度的 Benchmark，打通"公开原始数据 → 统一 Benchmark Case → Memory
System 评测"完整链路。本阶段不追求大量 Case：首版做成约 300 条，重点是验证数据结构与运行
链路，稳定后再扩到各维度 300–500 条。

固定维度与数据源：

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

数据流：`公开原始数据 → Source Adapter → Canonical Source Record → Dimension Builder →
Benchmark Case → System Adapter → Memory System → Evaluator`。

***

## 2. 第一阶段：数据收集与版本固定

### 2.1 D01/D02 LongMemEval

用官方 cleaned 版 `xiaowu0162/longmemeval-cleaned`（不要用 deprecated 的 `longmemeval`，
暂不切 LongMemEval-V2）。v0.1 只需两个文件，本地在 `E:\LRZ\_Workplace\fork\LongMemEval\data`：

```text
longmemeval_oracle.json       # 核查 Evidence / Gold Memory
longmemeval_s_cleaned.json    # 真实长期记忆构建与检索
```

不下载 `longmemeval_m_cleaned.json`。Adapter 不重写：先建 regression fixture 保语义一致，
再改清理路径、字段兼容、统一 Core Schema 与 Gold Payload 输出。

### 2.2 D03 LoCoMo

用官方 `snap-research/LoCoMo` 的 `data/locomo10.json`（含 10 个超长 conversation：session、
timestamp、turn、event summary、QA、evidence dialog id）。不要用第三方重格式化版本。本地在
`E:\LRZ\_Workplace\fork\LoCoMo\data`。重点核查字段（sample/session/dia_id/speaker/text/qa.* ）
保留正确；**`category` 数字映射必须按官方 evaluation code + 本地数据联合核验**，不能按论文
段落顺序硬编码。v0.1 过滤依赖真实 image 的 Case，只留纯文本 Evidence。

### 2.3 D04 PrefEval

三套 Hugging Face Dataset 全下（explicit / implicit_choice / implicit_persona，各 1000 条），
文件小且 D04 需要正负 Activation Case：

```text
siyanzhao/prefeval_explicit
siyanzhao/prefeval_implicit_choice
siyanzhao/prefeval_implicit_persona
```

### 2.4 D05 PersonaMem-v2

用 `bowen-upenn/PersonaMem-v2`，**只用 text + 32K chat history，不用 multimodal / 128K**（规模
变量统一交给 D07）。本地在 `E:\LRZ\_Workplace\fork\PersonaMem-v2\data`。需要：
`benchmark/text/benchmark.csv`、`data/chat_history_32k/`、`data/raw_data/`。Adapter 不重写，
优先改造为新的 Source Adapter Interface。v0.1 选样优先 `text only / updated=false /
sensitive_info=false / who=user / persona_id 不重复`（稳定画像），Preference update 交由 D06。

### 2.5 D06 MemoryAgentBench

用官方 `ai-hyz/MemoryAgentBench` 的 **Conflict_Resolution**（2025-09-29 后版本，已删高成本样本、
修复 `qa_pair_ids`），`data/Conflict_Resolution-00000-of-00001.parquet`（约 1.49 MB）。

**关键结构**：顶层仅 8 条 record，每条内含 `context / questions[] / answers[][] / metadata`
（metadata 含 demo/haystack_sessions/keypoints/previous_events/qa_pair_ids/question_dates/
question_ids/question_types/source）。不是 8 个样本：Source Adapter 保留 8 个 Context，Builder
展开成 Question-level，最终从 8 个 Context 抽 37 个 Conflict Case。

### 2.6 D07 BEAM

下载 `Mohammadta/BEAM` 与 `Mohammadta/BEAM-10M`。四个规模 100K/500K/1M/10M：普通版含 90 个
conversation（100K/500K/1M），BEAM-10M 单独 10 个；共约 100 conversation、2000 validated
probing questions，覆盖十种 memory ability。字段含 conversation_id/narratives/
user_profile/chat/probing_questions；`probing_questions` 是字符串，须用 `ast.literal_eval`
安全解析，不能 `eval`。10M 额外有 `plans[]`（各自含 conversation_seed/user_profile/chat/
plan_id），**不能假定与 100K/500K/1M 完全同构**。

### 2.7 D08 AgentMemBench

用官方 MemDialogue v2（release-verified，9170 个 memory event，带 meta + audit）：
`data/memdialogue_v2.jsonl`、`..._meta.json`、`..._audit.json`。不要从 WildChat 重建。事件结构：
`session_id/source_dataset/source_license/annotator_model/prompt_version/memory_events[(
turn_idx/event_type/raw_text/query/ground_truth/evidence_turn_indices/release_verified)]`。
MESA 本就含 Isolation & Privacy / Cross-user leak rate / GDPR deletion completeness，与 D08 匹配。

***

## 3. raw dataset 目录与 manifest

```text
datasets/raw/{longmemeval,locomo,prefeval/{explicit,implicit_choice,implicit_persona},
             personamem_v2,memoryagentbench,beam/{regular,10m},agentmembench}/...
datasets/manifests/{longmemeval,locomo,prefeval,personamem_v2,memoryagentbench,beam,agentmembench}.yaml
```

manifest 至少记录：`dataset_name / source_repo / source_revision / download_date / license /
files / file_hashes / adapter_version / notes`。**不要只记 main**，正式构建必须固定 commit SHA
或 HF revision。

***

## 4. 数据下载后统一 Audit

每套数据先跑 Dataset Audit，输出到 `reports/dataset_audit/*.json`（每源一个），通过后才写
Adapter。检查字段/类型/null 比例/唯一 ID/重复/Context·Session·Turn 长度分布/Question·Answer 数/
Evidence与Timestamp 可解析率/category 与 user 数量/异常 record；数组字段额外校验
`len(questions)==len(answers)==len(qa_pair_ids)`、question id 唯一、evidence id 真实存在。

***

## 5. Common Envelope 设计

**统一的是 Envelope，不是 Gold。** 每个 Dimension 自维护 Gold Payload。统一 Case 结构：

```text
schema_version
envelope:
    case_id / dimension_id / dimension_name
    source: dataset / revision / split / source_record_id
    identity: context_id / user_id / tenant_id
    context: context_ref / event_start / event_end / event_count / token_count
    query: query_id / text / timestamp
    metadata: language / difficulty / tags / selection_seed
gold:
    payload_type
    payload
```

`user_id / tenant_id / timestamp` 允许为空但字段必须固定存在。

***

## 6. 为什么用 context_ref 而非复制 Context

LongMemEval / BEAM / MemoryAgentBench 都有一 Context 多 Question。Case 内复制会导致
`BEAM-10M Context × 几十个 Question = 大量重复`。因此维度目录拆 `contexts/` 与 `cases/`，
Case 只保留 `context_ref`（如 `contexts/beam_10m_003.jsonl`），Runner 运行时加载，支持
多 Query / 一次 ingest 多次 query / context cache / 成本统计。

***

## 7. Canonical Event Schema

统一事件：

```text
event_id / session_id / turn_id / order / timestamp / role / content / source_ref / metadata
```

映射示例：LoCoMo `dia_id`→turn_id/source_ref；LongMemEval 与 BEAM chat turn→role/content；
MemoryAgentBench document chunk→`role: document`。**不要为凑 user/assistant 伪造 role。**

***

## 8. 各维度 Gold Payload

### D01 write

```text
payload_type: write
payload:
    scored_event_ids
    gold_memories[]: memory_id / canonical_content / memory_type / evidence_event_ids
    non_memory_event_ids
```

memory_type 首版：`personal_fact / preference / event / plan / goal / constraint /
relationship / decision / other`。指标：Write Precision / Recall。

**特殊处理**：LongMemEval Evidence 只证明"哪些内容能答某 Question"，不能直接等价于"应写入
Memory"，故 D01 需人工 Gold Memory Annotation。每个 Case 用"Evidence Session + 邻近
Distractor + 少量普通 Session"组成有限 Scoring Window，再人工标注窗口内应写入的 Memory；
否则把非 Evidence 内容当"不该记"会产生错误 Gold。（9/1 已完成 38 case 人工核验）

### D02 retrieval

```text
payload_type: retrieval
payload:
    gold_evidence_ids
    gold_answer
    retrieval_k: 1 / 3 / 5 / 10
```

指标：Hit@K / Recall@K / MRR。不重复标注答案，直接用 LongMemEval 自带 Gold Evidence。
v0.1：20 Information Extraction + 18 Multi-session Reasoning；尽量不混入 Knowledge
Update / Temporal，保持纯 Retrieval。

### D03 temporal

```text
payload_type: temporal
payload:
    gold_answer / evidence_event_ids / temporal_relations / evidence_time / query_time
    time_gap_days
    lifecycle: valid_from / valid_until / deleted_at / expected_active
```

LoCoMo 原生提供 session 顺序/timestamp/evidence dia_id/QA → 测 Temporal Accuracy、Long-gap
Recall；无删除协议，生命周期由 Builder 受控构造（原始事件 → 加 forget → 未来 Query，
`expected_active:false, deleted_at:T`）→ 测 Deleted Hit Rate。v0.1 38 case：
24 原生 Temporal + 8 Cross-session long-gap + 6 Derived lifecycle，按 time_gap_days 分桶。

### D04 activation

```text
payload_type: activation
payload:
    should_activate
    required_memory_ids
    preference
    answer_criteria
```

指标：Activation Precision / Recall / False Activation Rate / Utilization / E2E Accuracy。
Precision 必须保留（否则每 Query 都调 Memory 也能拿高 Recall）。v0.1 38 case = 19 true + 19
false；Positive 从 implicit_choice/implicit_persona 抽（Preference 在历史 Conversation，最终
Query 不重复，须依赖长期 Memory）；Negative 从 explicit 建（preference 已在当前输入附近，无需
长期历史），测系统是否无条件 Activation。

### D05 profile

```text
payload_type: profile
payload:
    profile_snapshot_time
    profile_items[]: profile_id / slot / value / evidence_event_ids / status
    gold_answer
    target_preference_ids
```

slot 首版：`preference/personal_fact/goal/constraint/habit/occupation/relationship/
communication_style/other`。v0.1 选 37 个不同 persona_id，各 3–8 个 Profile Item + 1 个最终
Personalized Query；优先 `updated=false / sensitive_info=false`，与 D06 解耦。指标：Profile
Precision / Preference Recall / Profile Consistency / Personalized Answer Accuracy。（9/1 已完成）

### D06 conflict

```text
payload_type: conflict
payload:
    gold_answer / conflict_type
    fact_versions[]: fact_id / value / order / timestamp / status
    winning_fact_ids
    stale_fact_ids
```

Source Adapter 保留原始 context/questions/answers/metadata；Builder 展开为 Question Case，并
从 `previous_events / keypoints / question_dates / question_types / context` 重建冲突链。校验
`questions[i]/answers[i]/qa_pair_ids[i]/question_types[i]` 严格一一对应。v0.1 从 8 个 Context
展开 37 Case，尽力单跳/多跳各半。指标：Latest-value / Conflict Resolution Acc / Stale Retrieval。

### D07 scale

```text
payload_type: scale
payload:
    scale_group_id / scale_level / target_tokens / gold_answer / gold_evidence_ids
    paired_anchor_id / expected_retrievable
```

**Recall Degradation 必须来自同一 conversation 的 Paired Scale Case**：不同规模不是同一 Context，
直接比无意义。理想：同一 BEAM-10M conversation 中取 Evidence 较早的 probing question，逐步扩大
后续 Distractor，使 Gold Evidence/Question/Answer 不变、仅 Context Size 变，得 Recall@K at
100K/500K/1M/10M 之间的退化。v0.1：32 Case（8 scale_group × 4 scale）+ 5 个 10M Stress Case。
若本地无法可靠定位 Evidence，**不强行生成 paired、不伪造 Evidence**，D07 退化为 Accuracy@Scale /
Recall@K@Scale / Latency / Cost。

### D08 privacy

```text
payload_type: privacy
payload:
    scenario_type / owner_user_id / querying_user_id
    allowed_memory_ids / forbidden_memory_ids / deleted_memory_ids / canary_tokens
```

Builder 负责跨用户组合。v0.1 37 case：19 Cross-user Isolation + 10 Deletion + 8 Forbidden
Canary Exposure。Canary 用人工生成、无现实意义、全局唯一 Token（如 `PRIVATE_CANARY_A_0042`）
做泄漏检测，不用真实敏感数据；Deletion 校验"删除前确实存在"。指标：Cross-user Leakage /
Deleted Memory Hit / Deletion Completeness / Forbidden Canary Exposure。（9/2 已完成）

***

## 17. Source Adapter

目录 `src/sources/{base,longmemeval,locomo,prefeval,personamem_v2,memoryagentbench,beam,
agentmembench}.py`，统一接口：`load_raw() / audit() / normalize() / validate() /
iter_records()`。只解决"原数据怎么读、字段语义、映射 Canonical Event、如何保存 Source ID 与
Source Gold"。**不负责**最终抽几 Case、正负/难度比例、寿命/Activation/Scale/Privacy Pair、指标
——这些全部属于 Dimension Builder。

## 18. 已有三个 Adapter 的迁移策略

原则：**能改不重写、能包 Wrapper 不动内部、先保证旧测试继续通过**。

- LongMemEval：建 fixture → 升级 cleaned 路径 → 挂 SourceAdapter Interface → 输出 Canonical
  Event → 加 source metadata。
- LoCoMo：建 fixture → 保留 Session 与 Timestamp → 核查 category mapping → 输出 Canonical Event。
- PersonaMem-v2：建 fixture → 锁定 text+32K → 建 persona_id→raw_data/history 索引 → 加 profile
  source metadata。

## 19. 新增四套 Adapter 的开发优先级

顺序：**PrefEval → MemoryAgentBench → AgentMemBench → BEAM**。PrefEval 结构最小最易，验证新
Interface；MemoryAgentBench 小但 nested array、一 Context 多 Case 典型；AgentMemBench 事件规整，
验证 multi-user/delete/privacy；BEAM 复杂度最高（多 Scale+超长+10M 特殊结构+probing 字符串
解析），不要作为新框架首套实现。

## 20. Source Adapter 输出目录

`datasets/staging/{d01_write…d08_privacy}/`，各含 `contexts/` + `records.jsonl`。仍是 Staging：
可追溯、结构统一、保留原始 Source ID 与全部 Gold Candidate，但还不是最终 Benchmark。

## 21. Dimension Builder

目录 `src/dimensions/{base,d01_write…d08_privacy}.py`，统一接口：`load_candidates() /
filter_candidates() / derive_gold() / sample_cases() / validate_cases() / build()`。承担真正
Benchmark 逻辑：如 PrefEval Adapter 只知道 preference/conversation/question，D04 Builder 才定
`should_activate`；AgentMemBench Adapter 不知道哪两个 user 组 Privacy Case，D08 Builder 才跨用户组合。

## 22. 最终 Benchmark 目录

```text
datasets/benchmark/v0_1/
    manifest.yaml
    {d01_write…d08_privacy}/contexts/ + cases.jsonl
```

## 23. Builder 完成后的完整核查

生成后必须 Audit：共 300（D01–D04=38，D05–D08=37）；校验 case_id 全局唯一、context_ref 存在、
source_record_id 可回溯、query 非空、Gold Payload 与维度匹配、Evidence ID 可解析、无重复 case、
**无 Source Gold 泄漏进 Query、无 Answer 泄漏进 Context Metadata**。D04 Positive/Negative=19/19；
D07 同 scale_group 的 Query/Answer/Gold Evidence 一致且 Scale 单调增；D08 owner≠querying、
forbidden/deleted 存在、Canary 全局唯一。

## 24. System Adapter + 25. 推荐接口

目录 `src/systems/{base,reme}.py`，当前只支持 ReMe，不重写（现有链路已通）。接口：
`reset/create_namespace/ingest/search/query/list_memories/delete/get_profile/get_trace/
get_stats/cleanup`，并带 capability：
`write_trace / retrieval / activation_trace / profile / delete / user_isolation /
latency_stats / cost_stats`。不同维度观察不同能力（D01=list_memories、D02=search、
D04=get_trace、D08=delete+namespace）。**系统不支持某能力时 Evaluator 返回 `unsupported`，不要
自动记 0**，否则评的是 API 而非 Memory 能力。

## 26. ReMe Adapter 修改原则

保持现有 LongMemEval→ReMe ingestion/query 稳定；用 `ReMeSystemAdapter` Wrapper 包现有
`ReMeAdapter`，只补 namespace/trace/list memory/delete/stats。缺什么补什么，不为统一接口重写
已通过测试的 ingestion/query。

## 27. Runner

流程：`Benchmark Case → 加载 context_ref → reset → ingest → 执行 Dimension-specific Action →
记录 Trace → Evaluator → Result`。Result 统一 Envelope：`run_id/case_id/dimension_id/system/
system_version/prediction/retrieved_memories/trace/latency(ingest,retrieval,answer,total)/
cost(input,output,api)/metrics/status/error`。

## 28. Context Cache

因 LongMemEval/MemoryAgentBench/BEAM 一 Context 多 Query，支持 `context_id` + `reuse_context`。
正式评分仍保证 Case 独立；性能测试可用 Context Batch Mode（`ingest once, query N times`）。
两种模式分开记录，不混比。

## 29–30. 测试

建议目录 `tests/{sources,dimensions,systems,integration}/`。每个 Source Adapter 至少：
`test_load_raw/record_count/required_fields/unique_ids/normalize/source_traceability/
context_reference/gold_reference/deterministic_output`；已有三个 Adapter 额外加
`test_legacy_equivalence` 防迁移破坏。

## 31. 固定随机抽样

所有抽卡固定 `selection_seed: 20260901`，把选中的 `source_record_id / source_question_id`
写入 manifest，使 v0.1 完全可复现。

## 32. v0.1 开发顺序

1. 确认本地 LongMemEval（是否 cleaned）/LoCoMo/PersonaMem-v2
2. 下载 PrefEval×3、MemoryAgentBench Conflict、BEAM、BEAM-10M、AgentMemBench
3. 运行 Dataset Audit（此时不改 Benchmark Logic）
4. 定义并冻结 Core Envelope / Canonical Event / 八套 Gold Payload v0.1
5. 迁移 LongMemEval/LoCoMo/PersonaMem Adapter（先建 fixture）
6–9. 依次实现 PrefEval → MemoryAgentBench → AgentMemBench → Beam Adapter
10. 通过后生成 `datasets/staging/`
11. 依次实现 D01–D08 Builder
12. 生成 `datasets/benchmark/v0_1/`（300 Case）
13. 执行 Benchmark Audit（不过 Audit 不进评测）
14. 用 Wrapper 包 ReMe → ReMeSystemAdapter
15. 先跑最成熟的 D02 LongMemEval 验证不破坏现有结果
16. 依次接 D01/D03/D04/D05/D06/D08，最后 D07（成本最高）

## 33. v0.1 完成标准

不以高分位完成标准，达成即可：

- 数据层：7 套源固定版本、300 Case 构建成功、全可回溯、8 种 Gold 完整、Audit 100% 通过。
- Adapter 层：7 Source Adapter + 8 Dimension Builder + 1 ReMe System Adapter，已有三套以改为主。
- 运行层：每个维度至少跑通一次 Load/Ingest/Query|Inspect/Evaluate/Save。
- 指标层：D01 Write P/R；D02 Hit@K/Recall@K/MRR；D03 Temporal Acc/Long-gap Recall/Deleted Hit；
  D04 Activation P/R/Utilization/E2E；D05 Profile P/Preference Recall/Consistency；D06 Latest-value/
  Conflict Res/Stale Retrieval；D07 Recall@Scale/Degradation（仅 paired 计算）/P95 Latency/Cost；D08
  Leakage/Deletion/Forbidden Canary。

## 34. 最重要的工程约束

1. 不再新增公开数据集，先把 8 维骨架跑通。
2. 统一的是 Core Envelope，不是 Raw Dataset 字段。
3. Source Adapter 不写 Benchmark 策略，只忠实理解公开数据。
4. 所有采样/正负样本/寿命/Scale/Privacy Pair 都在 Dimension Builder。
5. System Adapter 永远不关心数据来自哪个 benchmark，只收统一 Context/Event/Query/Action。
6. 已有代码优先兼容升级（LongMemEval/LoCoMo/PersonaMem-v2/ReMe 都不推倒重写）。
7. D01 Gold Memory 是首版最需人工审核的部分。
8. D07 Recall Degradation 必须来自 Paired Scale Case，不得拿不同 BEAM 100K vs 10M 冒充。
9. D04 必须同时有 Activation Positive 与 Negative，否则无法识别无条件调用 Memory。
10. v0.1 的真正目标是一个稳定闭环
    `Raw Dataset→Source Adapter→Canonical Record→Dimension Builder→300 Benchmark Cases→
    ReMe System Adapter→8 Dimension Evaluation`。闭环稳定后，扩到 3000 条主要是抽样、Gold 标注
    与质控，不再改底层架构。