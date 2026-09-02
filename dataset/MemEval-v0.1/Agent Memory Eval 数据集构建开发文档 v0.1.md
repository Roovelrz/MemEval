# Agent Memory Eval 数据集构建开发文档 v0.1

## 1. 项目目标与范围

本阶段目标是构建一套包含 8 个记忆能力维度的 Agent Memory Evaluation Dataset，并完成从公开原始数据到统一 Benchmark Case，再到具体 Memory System 的完整评测链路。

当前固定维度与数据源如下：

| ID  | 测试维度      | 主数据集             |
| --- | --------- | ---------------- |
| D01 | 记忆抽取与写入   | LongMemEval      |
| D02 | 基础长期记忆    | LongMemEval      |
| D03 | 长时间跨度对话   | LoCoMo           |
| D04 | 主动调用与记忆使用 | PrefEval         |
| D05 | 用户画像与偏好   | PersonaMem-v2    |
| D06 | 动态更新与冲突   | MemoryAgentBench |
| D07 | 超大规模长上下文  | BEAM             |
| D08 | 隐私与用户隔离   | AgentMemBench    |

总体设计原则为：

公开原始数据\
↓\
Source Adapter\
↓\
Canonical Source Record\
↓\
Dimension Builder\
↓\
Benchmark Case\
↓\
System Adapter\
↓\
Memory System\
↓\
Evaluator

本阶段不追求大量 Case。首先完成约 300 Case 的 v0.1 数据集，使 8 个维度全部能够完整经过数据构建、系统运行、结果记录和指标计算流程。

建议首版数量：

| 维度  | Case 数 |
| --- | -----: |
| D01 |     38 |
| D02 |     38 |
| D03 |     38 |
| D04 |     38 |
| D05 |     37 |
| D06 |     37 |
| D07 |     37 |
| D08 |     37 |
| 合计  |    300 |

首版重点不是统计显著性，而是验证数据结构和运行链路。300 Case 稳定以后，再将各维度扩展到约 300 至 500 Case。

***

# 2. 第一阶段：公开数据集收集与版本固定

## 2.1 D01、D02 LongMemEval

### 使用版本

使用：

`xiaowu0162/longmemeval-cleaned`

不要继续基于旧版：

`xiaowu0162/longmemeval`

官方已经将旧数据标记为 deprecated，并明确推荐使用 cleaned 版本。cleaned 版本修复了部分 history session 对答案正确性的干扰。

暂时不要切换到 LongMemEval-V2。LongMemEval-V2 是 2026 年发布的另一套 agentic 场景 benchmark，任务结构已经发生较大变化。当前项目已经有 LongMemEval Adapter 和 ReMe 跑通经验，v0.1 阶段保持 LongMemEval v1 cleaned 更利于控制变量。

### v0.1 需要的文件

只需要：

```
longmemeval_oracle.json
longmemeval_s_cleaned.json
```

本地存放在：E:\LRZ\_Workplace\fork\LongMemEval\data

暂时不下载或不处理 `longmemeval_m_cleaned.json`。

其中：

`oracle` 用于核查 Evidence 和 Gold Memory。

`longmemeval_s_cleaned` 用于真实长期记忆构建和检索。

官方当前也使用这几个 cleaned 文件。

### 本地已有代码处理原则

LongMemEval Adapter 不重写。

首先建立 regression test：

```text
旧 Adapter
    ↓
读取现有 LongMemEval
    ↓
输出现有 normalized record
    ↓
保存 fixture
```

之后仅修改：

```text
文件路径兼容
字段兼容
cleaned 数据兼容
统一 Core Schema 输出
Gold Payload 输出
```

修改后要求旧 fixture 中核心字段保持语义一致。

***

# 2.2 D03 LoCoMo

### 使用版本

使用官方仓库：

`snap-research/LoCoMo`

固定使用：

```text
data/locomo10.json
```

这是当前正式 benchmark release，包含 10 个超长期 conversation。每个 conversation 内含 session、session timestamp、turn、event summary、QA 和 evidence dialog id。

不要使用第三方重新格式化版本作为原始输入。

### 本地已有代码处理原则

已有 LoCoMo Adapter 继续复用。

本地存放在：E:\LRZ\_Workplace\fork\LoCoMo\data

重点检查现有代码是否已经正确保留：

```text
sample_id
session_id
session_date_time
dia_id
speaker
text
qa.question
qa.answer
qa.category
qa.evidence
```

尤其注意 `category` 数字映射。LoCoMo 的 JSON category id 与论文正文枚举顺序容易混淆，已有公开核查指出 JSON 中 `2` 对应 Temporal，其他类别同样存在编号与论文描述顺序不一致的问题。最终必须以官方 evaluation code 和本地数据联合核验，不允许根据论文段落顺序直接硬编码。

v0.1 暂时过滤依赖真实 image 的 Case，只保留纯文本 Evidence。

***

# 2.3 D04 PrefEval

这是第一套需要从零构建 Adapter 的数据。

### 下载版本

PrefEval 官方实际上拆成三套 Hugging Face Dataset：

```text
siyanzhao/prefeval_explicit
siyanzhao/prefeval_implicit_choice
siyanzhao/prefeval_implicit_persona
```

每种 preference form 各 1000 条。

三套全部下载，因为文件很小，而且 D04 后面正好需要构造正负 Activation Case。

### 三种数据结构

Explicit：

```text
preference
question
explanation
topic
preference_type
```

Implicit Choice：

```text
preference
question
explanation
implicit_query
options
aligned_op
topic
conversation_query
conversation_assistant_options
conversation_user_selection
conversation_assistant_acknowledgment
```

Implicit Persona：

```text
preference
question
explanation
persona
topic
conversation
preference_type
```

官方明确将 PrefEval 设计为 explicit、implicit choice 和 implicit persona 三类。

***

# 2.4 D05 PersonaMem-v2

### 使用版本

继续使用：

`bowen-upenn/PersonaMem-v2`

当前 v0.1 只使用 text 数据，不使用 multimodal。

<br />

本地存放在：E:\LRZ\_Workplace\fork\PersonaMem-v2\data

<br />

需要：

```text
benchmark/text/benchmark.csv
data/chat_history_32k/
data/raw_data/
```

暂时不需要：

```text
benchmark/text/train.csv
benchmark/text/val.csv
chat_history_128k/
multimodal/*
```

官方 text benchmark 有 5000 个 benchmark query，并通过 persona\_id 与 chat history、preference、related snippet 等内容关联。

32K chat history 已经足以测试 Profile，不需要在 D05 同时引入规模变量。规模统一交给 D07。

### 本地已有代码处理原则

PersonaMem-v2 Adapter 不重写。

优先将现有 Adapter 改造成新的 Source Adapter Interface。

v0.1 选样优先：

```text
text only
updated = false
sensitive_info = false
who = user
persona_id 不重复
```

先测试稳定用户画像。

Preference update 暂不在 D05 展开，因为 D06 已经专门负责动态更新与冲突。

***

# 2.5 D06 MemoryAgentBench

这是第二套需要从零处理的数据。

### 使用版本

使用官方：

`ai-hyz/MemoryAgentBench`

只下载：

```text
Conflict_Resolution
```

当前正式版本是 2025 年 9 月 29 日以后更新过的数据。官方删除了一部分高成本和低效率样本，并修复过 `qa_pair_ids`。

具体文件：

```text
data/Conflict_Resolution-00000-of-00001.parquet
```

当前文件约 1.49 MB。

### 一个重要结构

Conflict Resolution 顶层只有 8 条 record。

但每条 record 内部不是一个 Case，而是：

```text
context
questions[]
answers[][]
metadata
```

完整 metadata 包括：

```text
demo
haystack_sessions
keypoints
previous_events
qa_pair_ids
question_dates
question_ids
question_types
source
```

所以不能认为只有 8 个测试样本。

Source Adapter 要首先保持这 8 个 Context。

Dimension Builder 再展开：

```text
context 0 + question 0
context 0 + question 1
context 0 + question 2
...
```

最终从 8 个 Context 中抽取 37 个独立 Conflict Case。

官方本身采用的也是一次注入长 Context，再回答多 Question 的设计。

***

# 2.6 D07 BEAM

这是第三套需要从零处理的数据。

### 下载两个官方数据集

```text
Mohammadta/BEAM
Mohammadta/BEAM-10M
```

BEAM 当前公开四个规模：

```text
100K
500K
1M
10M
```

其中 Hugging Face 普通 BEAM 包含 100K、500K、1M，共 90 个 conversation。

BEAM-10M 单独包含 10 个 conversation。

BEAM 总体包含 100 个 conversation 和约 2000 个 validated probing questions，并覆盖十种 memory ability。

### 主要字段

普通 BEAM：

```text
conversation_id
conversation_seed
narratives
user_profile
conversation_plan
user_questions
chat
probing_questions
```

其中 `probing_questions` 仍然是字符串，需要 Adapter 使用安全 parser 转换，不能直接 `eval`。官方示例使用 `ast.literal_eval`。

10M 的结构额外包含：

```text
plans[]
```

每个 plan 内又有独立：

```text
conversation_seed
user_profile
chat
plan_id
```

因此 10M Adapter 不能假定与 100K、500K、1M 完全同构。

***

# 2.7 D08 AgentMemBench

这是第四套需要从零处理的数据。

### 使用版本

使用官方仓库当前正式发布：

```text
AgentMemBench
MemDialogue v2
```

需要保留：

```text
data/memdialogue_v2.jsonl
data/memdialogue_v2_meta.json
data/memdialogue_v2_audit.json
```

不要在 v0.1 阶段重新从 WildChat 构建 MemDialogue。

官方已经提供 release-verified 的 MemDialogue v2，共 9170 个 memory event，并且附带 meta 和 deterministic audit 文件。

每条基本结构包括：

```text
session_id
source_dataset
source_license
annotator_model
prompt_version

memory_events:
    turn_idx
    event_type
    raw_text
    query
    ground_truth
    evidence_turn_indices
    release_verified
```

AgentMemBench 的 MESA 已经明确包含：

```text
Isolation & Privacy
Cross-user leak rate
GDPR deletion completeness
```

所以它和 D08 的目标高度匹配。

***

# 3. 推荐的 raw dataset 目录

```text
datasets/
    raw/
        longmemeval/
        locomo/
        prefeval/
            explicit/
            implicit_choice/
            implicit_persona/
        personamem_v2/
        memoryagentbench/
        beam/
            regular/
            10m/
        agentmembench/
```

再增加：

```text
datasets/
    manifests/
        longmemeval.yaml
        locomo.yaml
        prefeval.yaml
        personamem_v2.yaml
        memoryagentbench.yaml
        beam.yaml
        agentmembench.yaml
```

每个 manifest 至少记录：

```text
dataset_name
source_repo
source_revision
download_date
license
files
file_hashes
adapter_version
notes
```

不要只记录 main。

正式构建数据时必须固定实际 commit SHA 或 Hugging Face revision。

***

# 4. 数据下载后的统一核查流程

下载完成后，不要马上写 Adapter。

先为每套数据运行 Dataset Audit。

建议统一输出：

```text
reports/dataset_audit/
    longmemeval.json
    locomo.json
    prefeval.json
    personamem_v2.json
    memoryagentbench.json
    beam.json
    agentmembench.json
```

每个 Audit 至少检查：

```text
总记录数
字段列表
字段类型
null 比例
唯一 ID 数
重复记录
Context 长度分布
Session 数量分布
Turn 数量分布
Question 数量
Answer 数量
Evidence 可解析率
Timestamp 可解析率
不同 category 数量
不同 user 数量
异常 record
```

对数组字段额外检查：

```text
len questions == len answers
len questions == len qa_pair_ids
question id 是否唯一
evidence id 是否真实存在
```

所有 Dataset Audit 通过以后，才能进入 Source Adapter。

***

# 5. Common Envelope 设计

不建议把所有 Dimension 的 Gold 强行统一。

统一的是 Envelope。

每个 Dimension 自己维护 Gold Payload。

统一 Case 推荐结构：

```text
schema_version

envelope:
    case_id
    dimension_id
    dimension_name

    source:
        dataset
        revision
        split
        source_record_id

    identity:
        context_id
        user_id
        tenant_id

    context:
        context_ref
        event_start
        event_end
        event_count
        token_count

    query:
        query_id
        text
        timestamp

    metadata:
        language
        difficulty
        tags
        selection_seed

gold:
    payload_type
    payload
```

其中：

`user_id` 可以为空。

`tenant_id` 可以为空。

`timestamp` 可以为空。

但字段本身固定存在。

***

# 6. 为什么使用 context\_ref 而不是把完整 Context 放进每个 Case

LongMemEval、BEAM、MemoryAgentBench 都存在多个 Question 共用同一个 Context 的情况。

如果 Case 内直接复制 Context，会导致：

```text
BEAM 10M Context
×
几十个 Question
=
大量重复数据
```

因此建议：

```text
dimension/
    contexts/
    cases/
```

Case 只保留：

```text
context_ref
```

例如：

```text
context_ref: contexts/beam_10m_003.jsonl
```

Runner 在运行时加载 Context。

这样同时支持：

```text
同一 Context 多 Query
一次 ingest 多次 query
Context cache
运行成本统计
```

***

# 7. Canonical Event Schema

所有 Source Adapter 最终都尽量映射到一个统一 Event：

```text
event_id
session_id
turn_id
order
timestamp
role
content
source_ref
metadata
```

例如：

LoCoMo 的 `dia_id` 映射：

```text
turn_id
source_ref
```

LongMemEval message 映射：

```text
role
content
```

BEAM chat turn 同样映射：

```text
role
content
```

MemoryAgentBench 如果原始输入是 document chunk，可以设置：

```text
role: document
```

不要为了满足 user 或 assistant 格式而伪造 conversation role。

***

# 8. 各维度独立 Gold Payload

## D01 记忆抽取与写入

```text
gold:
    payload_type: write

    payload:
        scored_event_ids

        gold_memories:
            memory_id
            canonical_content
            memory_type
            evidence_event_ids

        non_memory_event_ids
```

建议 memory\_type 第一版只保留：

```text
personal_fact
preference
event
plan
goal
constraint
relationship
decision
other
```

指标：

```text
Write Precision
Write Recall
```

### D01 特殊处理

LongMemEval 原始 Evidence 只能说明哪些内容能够回答特定 Question。

它不能直接证明完整 Context 中哪些内容应该写入 Memory。

因此 D01 必须增加一层人工 Gold Memory Annotation。

v0.1 的 38 Case 不处理完整十万 Token Context。

每个 Case 选择：

```text
Evidence Session
+
邻近 Distractor Session
+
少量普通 Session
```

组成一个有限 Scoring Window。

然后人工标注该窗口中所有应该写入的 Memory。

这样才能真正计算 Write Precision。

否则把非 Evidence 内容直接当成不应该记忆，会产生错误 Gold。

建议 38 个 D01 Case 全部人工复核。

***

# 9. D01 v0.1 选样

38 Case 建议：

```text
19 Information Extraction
10 Knowledge Update
9 Multi-session Reasoning
```

目的不是评估对应 QA 能力，而是获得不同类型的可记忆事实。

每个 Case 建议：

```text
8 至 30 turns
2 至 8 Gold Memory
若干 non-memory turns
```

暂时不使用 Abstention。（9/1已完成D01 38case的人工核验）

***

# 10. D02 基础长期记忆 Gold

```text
gold:
    payload_type: retrieval

    payload:
        gold_evidence_ids
        gold_answer
        retrieval_k:
            1
            3
            5
            10
```

指标：

```text
Hit@K
Recall@K
MRR
```

D02 不需要重新标注答案。

直接使用 LongMemEval 自带 Gold Evidence。

v0.1：

```text
20 Information Extraction
18 Multi-session Reasoning
```

尽量不要把 Knowledge Update 和 Temporal 混进来，否则 D02 不再是纯 Retrieval 测试。

***

# 11. D03 长时间跨度对话 Gold

```text
gold:
    payload_type: temporal

    payload:
        gold_answer
        evidence_event_ids
        temporal_relations
        evidence_time
        query_time
        time_gap_days

        lifecycle:
            valid_from
            valid_until
            deleted_at
            expected_active
```

LoCoMo 原生可以直接提供：

```text
Session chronological order
Timestamp
Evidence dia_id
Question
Answer
```

因此原生部分测试：

```text
Temporal Accuracy
Long-gap Recall
```

但是 LoCoMo 没有完整原生 Memory Delete protocol。

所以生命周期部分由 LoCoMo Builder 受控构造。

例如：

```text
原始事件 A
↓
后续添加 forget event
↓
未来 Query
```

Gold 设置：

```text
expected_active: false
deleted_at: T
```

这样仍然只使用 LoCoMo 一个数据源，但可以测试 Deleted Hit Rate。

v0.1 的 38 Case 建议：

```text
24 原生 Temporal
8 Cross-session long-gap
6 Derived lifecycle
```

并根据实际 `time_gap_days` 做分桶抽样。

***

# 12. D04 主动调用与记忆使用 Gold

```text
gold:
    payload_type: activation

    payload:
        should_activate
        required_memory_ids
        preference
        answer_criteria
```

指标：

```text
Activation Precision
Activation Recall
False Activation Rate
Utilization Rate
E2E Accuracy
```

Activation Precision 必须保留。

否则系统每个 Query 都调用 Memory，也可以获得非常高的 Activation Recall。

### v0.1 构造

38 Case：

```text
19 should_activate = true
19 should_activate = false
```

Positive 优先从：

```text
implicit_choice
implicit_persona
```

抽取。

Preference 位于历史 Conversation。

最终 Query 本身没有明确重复 Preference。

因此回答必须依赖长期 Memory。

Negative 优先从：

```text
explicit
```

构建。

Preference 已经出现在当前输入附近，不依赖长期历史即可正确回答。

这样可以测试系统是否存在无意义 Memory Activation。

***

# 13. D05 用户画像与偏好 Gold

```text
gold:
    payload_type: profile

    payload:
        profile_snapshot_time

        profile_items:
            profile_id
            slot
            value
            evidence_event_ids
            status

        gold_answer
        target_preference_ids
```

第一版 slot 不需要设计得太复杂。（9/1已完成）

建议：

```text
preference
personal_fact
goal
constraint
habit
occupation
relationship
communication_style
other
```

v0.1 选择 37 个不同 `persona_id`。

每个 Persona：

```text
3 至 8 个 Gold Profile Item
1 个最终 Personalized Query
```

优先：

```text
updated = false
sensitive_info = false
```

目的就是将 D05 与 D06 的动态更新能力解耦。

指标：

```text
Profile Precision
Preference Recall
Profile Consistency
Personalized Answer Accuracy
```

***

# 14. D06 动态更新与冲突 Gold

Source Adapter 首先保留 MemoryAgentBench 原始：

```text
context
questions
answers
metadata
```

Dimension Builder 再将 8 个 Context 展开为 Question-level Case。

Gold：

```text
gold:
    payload_type: conflict

    payload:
        gold_answer
        conflict_type

        fact_versions:
            fact_id
            value
            order
            timestamp
            status

        winning_fact_ids
        stale_fact_ids
```

优先从以下字段重建冲突链：

```text
previous_events
keypoints
question_dates
question_types
context
```

必须检查：

```text
questions[i]
answers[i]
qa_pair_ids[i]
question_types[i]
```

是否严格一一对应。

v0.1 从 8 个原始 Context 展开 37 个 Question Case。

尽量做到：

```text
约一半 single-hop conflict
约一半 multi-hop conflict
```

实际比例以下载后的 `question_types` Audit 为准。

指标：

```text
Latest-value Accuracy
Conflict Resolution Accuracy
Stale Retrieval Rate
```

***

# 15. D07 超大规模长上下文 Gold

普通直接抽取 100K、500K、1M、10M 不足以严格计算 Recall Degradation。

因为不同规模的数据本身不是同一个 Context。

因此需要引入：

```text
scale_group_id
```

Gold：

```text
gold:
    payload_type: scale

    payload:
        scale_group_id
        scale_level
        target_tokens
        gold_answer
        gold_evidence_ids
        paired_anchor_id
        expected_retrievable
```

### v0.1 建议构造 37 Case

其中 32 Case：

```text
8 个 Scale Group
×
4 个 scale
=
32 Case
```

四档：

```text
100K
500K
1M
10M
```

理想情况是从同一个 BEAM 10M conversation 中选择 Evidence 较早出现的 probing question，然后逐步扩大后续 Distractor Context。

要求：

```text
Gold Evidence 不变
Question 不变
Answer 不变
只有 Context Size 改变
```

这样：

```text
Recall@K at 100K
Recall@K at 500K
Recall@K at 1M
Recall@K at 10M
```

之间的差才能称为 Recall Degradation。

剩余 5 Case 直接选择 10M Stress Case。

如果本地核查发现 BEAM probing question 无法可靠定位 Evidence，则 v0.1 不强行生成 paired degradation。

这时 D07 暂时输出：

```text
Accuracy by Scale
Recall@K by Scale
Retrieval Latency
Memory Build Latency
Token Cost
API Cost
```

严格 paired Recall Degradation 延后到 v0.2。

不能为了凑指标而伪造 Evidence。

***

# 16. D08 隐私与用户隔离 Gold

AgentMemBench 的 MemDialogue 负责提供 Memory Event。

Dimension Builder 负责重新组合用户。

Gold：

```text
gold:
    payload_type: privacy

    payload:
        scenario_type
        owner_user_id
        querying_user_id

        allowed_memory_ids
        forbidden_memory_ids
        deleted_memory_ids
        canary_tokens
```

v0.1 的 37 Case 建议：

```text
19 Cross-user Isolation
10 Deletion
8 Forbidden Canary Exposure
```

Cross-user Isolation：

```text
User A Memory
User B Memory
↓
Query A
↓
只能读取 A
```

Deletion：

```text
写入 Memory
↓
验证可召回
↓
Delete
↓
再次 Query
↓
不得召回
```

Forbidden Canary：

在不同 Tenant 中加入人工生成、完全无现实意义的唯一 Token。

例如：

```text
PRIVATE_CANARY_A_0042
```

然后测试 B 用户是否能够召回 A 用户的 Canary。

这样不需要使用真实敏感数据，也可以稳定检测 Leakage。

指标：

```text
Cross-user Leakage Rate
Deleted Memory Hit Rate
Deletion Completeness
Forbidden Canary Exposure Rate
```

AgentMemBench 本身也以 Cross-user leak rate 和 GDPR deletion completeness 作为 Isolation & Privacy 核心指标。(9/2已完成)

***

# 17. 第一层 Source Adapter

推荐目录：

```text
src/
    sources/
        base.py
        longmemeval.py
        locomo.py
        prefeval.py
        personamem_v2.py
        memoryagentbench.py
        beam.py
        agentmembench.py
```

统一接口：

```text
SourceAdapter

load_raw()
audit()
normalize()
validate()
iter_records()
```

Source Adapter 只解决：

```text
原数据怎么读
字段是什么意思
怎样映射成 Canonical Event
Source ID 如何保存
Source Gold 如何保存
```

Source Adapter 不负责：

```text
最终抽多少 Case
正负样本比例
难度比例
生命周期构造
Activation Pair
Scale Pair
Privacy Pair
最终指标
```

这些全部属于 Dimension Builder。

***

# 18. 已有三个 Adapter 的迁移策略

## LongMemEval

```text
现有 Adapter
↓
建立 fixture
↓
升级 cleaned 数据路径
↓
加入 SourceAdapter Interface
↓
增加 Canonical Event 输出
↓
增加 source metadata
```

## LoCoMo

```text
现有 Adapter
↓
建立 fixture
↓
保留 Session 与 Timestamp
↓
核查 category mapping
↓
增加 Canonical Event 输出
```

## PersonaMem-v2

```text
现有 Adapter
↓
建立 fixture
↓
锁定 text + 32K
↓
建立 persona_id 到 raw_data 和 history 的索引
↓
增加 profile source metadata
```

原则：

```text
能改不重写
能包一层 Wrapper 不动内部
先保证旧测试继续通过
```

***

# 19. 新增五套 Adapter 的开发优先级

推荐顺序：

```text
1. PrefEvalAdapter
2. MemoryAgentBenchAdapter
3. AgentMemBenchAdapter
4. BeamAdapter
```

实际是四个新的 Source Adapter，因为 LongMemEval、LoCoMo、PersonaMem 已经存在。

### 第一优先 PrefEval

结构小、数据少、最容易完成。

可以快速验证新 SourceAdapter Interface。

### 第二优先 MemoryAgentBench

数据量很小，但 nested array 和 context/query 分离结构比较典型。

适合验证：

```text
一个 Context
多个 Case
```

### 第三优先 AgentMemBench

事件结构非常规整。

适合验证：

```text
multi-user composition
delete
privacy
```

### 最后 BEAM

因为 BEAM 同时存在：

```text
多 Scale
超长 Context
10M 特殊结构
probing_questions string parsing
```

复杂度最高。

不要拿 BEAM 作为新 Adapter Framework 的第一套实现。

***

# 20. Source Adapter 输出目录

```text
datasets/
    staging/
        d01_write/
            contexts/
            records.jsonl

        d02_retrieval/
            contexts/
            records.jsonl

        d03_temporal/
            contexts/
            records.jsonl

        d04_activation/
            contexts/
            records.jsonl

        d05_profile/
            contexts/
            records.jsonl

        d06_conflict/
            contexts/
            records.jsonl

        d07_scale/
            contexts/
            records.jsonl

        d08_privacy/
            contexts/
            records.jsonl
```

这里还是 Staging Dataset。

它必须：

```text
可追溯
结构统一
保留原始 Source ID
保留所有 Gold Candidate
```

但还不是最终 Benchmark。

***

# 21. 第二层 Dimension Builder

目录：

```text
src/
    dimensions/
        base.py
        d01_write.py
        d02_retrieval.py
        d03_temporal.py
        d04_activation.py
        d05_profile.py
        d06_conflict.py
        d07_scale.py
        d08_privacy.py
```

统一接口：

```text
DimensionBuilder

load_candidates()
filter_candidates()
derive_gold()
sample_cases()
validate_cases()
build()
```

Builder 负责真正的 Benchmark Logic。

例如：

PrefEval Source Adapter 只知道：

```text
preference
conversation
question
```

D04 Builder 才决定：

```text
should_activate = true
```

或者：

```text
should_activate = false
```

同理：

AgentMemBench Source Adapter 不知道哪两个 User 应该组成 Privacy Case。

D08 Builder 才进行跨用户组合。

***

# 22. 最终 Benchmark 目录

```text
datasets/
    benchmark/
        v0_1/
            manifest.yaml

            d01_write/
                contexts/
                cases.jsonl

            d02_retrieval/
                contexts/
                cases.jsonl

            d03_temporal/
                contexts/
                cases.jsonl

            d04_activation/
                contexts/
                cases.jsonl

            d05_profile/
                contexts/
                cases.jsonl

            d06_conflict/
                contexts/
                cases.jsonl

            d07_scale/
                contexts/
                cases.jsonl

            d08_privacy/
                contexts/
                cases.jsonl
```

***

# 23. Dimension Builder 完成后的完整核查

生成 300 Case 后必须进行一次 Benchmark Audit。

检查：

```text
总 Case = 300

D01 = 38
D02 = 38
D03 = 38
D04 = 38
D05 = 37
D06 = 37
D07 = 37
D08 = 37
```

然后检查：

```text
case_id 全局唯一
context_ref 全部存在
source_record_id 全部可回溯
query 不为空
Gold Payload 与 dimension 匹配
Evidence ID 全部可以解析
无重复 Case
无 Source Gold 泄漏进入 Query
无 Answer 泄漏进入 Context Metadata
```

D04：

```text
Activation Positive = 19
Activation Negative = 19
```

D07：

```text
相同 scale_group 的 Query 一致
相同 scale_group 的 Answer 一致
Gold Evidence 一致
Scale 单调增加
```

D08：

```text
owner_user_id != querying_user_id
forbidden_memory_ids 存在
deleted_memory_ids 删除前确实存在
Canary 全局唯一
```

***

# 24. 第三层 System Adapter

目录：

```text
src/
    systems/
        base.py
        reme.py
```

当前只优先支持 ReMe。

不从头重写 ReMe Adapter。

因为现有 Adapter 已经能够完成：

```text
LongMemEval
↓
ReMe
↓
Evaluation
```

说明核心链路已经成立。

本阶段只把它扩展到统一接口。

***

# 25. System Adapter 推荐接口

```text
SystemAdapter

reset()
create_namespace()

ingest()
search()
query()

list_memories()
delete()

get_profile()
get_trace()
get_stats()

cleanup()
```

并增加 capability：

```text
capabilities:
    write_trace
    retrieval
    activation_trace
    profile
    delete
    user_isolation
    latency_stats
    cost_stats
```

这是必要的。

因为不同 Dimension 需要观察系统不同内部能力。

例如：

D01：

```text
list_memories
```

D02：

```text
search
```

D04：

```text
get_trace
```

D08：

```text
delete
user namespace
```

如果某个 Memory System 不支持某项能力，Evaluator 应返回：

```text
unsupported
```

不要自动记 0 分。

否则是在评估 API 能力，而不是 Memory 能力。

***

# 26. ReMe Adapter 的修改原则

现有稳定链路保持：

```text
LongMemEval
↓
现有 ReMe ingestion
↓
现有 ReMe retrieval/query
```

优先通过 Wrapper 方式兼容新的 SystemAdapter。

例如：

```text
ReMeSystemAdapter
    ↓
调用现有 ReMeAdapter
```

只补：

```text
namespace
trace
list memory
delete
stats
```

缺什么补什么。

不要为了统一接口重写已经通过 LongMemEval 测试的 ingestion 和 query 部分。

***

# 27. Runner 设计

最终 Runner：

```text
Benchmark Case
↓
加载 context_ref
↓
SystemAdapter.reset
↓
SystemAdapter.ingest
↓
执行 Dimension-specific Action
↓
记录 Trace
↓
Evaluator
↓
Result
```

Result 统一 Envelope：

```text
run_id
case_id
dimension_id
system
system_version

prediction
retrieved_memories
trace

latency:
    ingest
    retrieval
    answer
    total

cost:
    input_tokens
    output_tokens
    api_cost

metrics

status
error
```

***

# 28. Context Cache

由于：

```text
LongMemEval
MemoryAgentBench
BEAM
```

都可能出现一个 Context 对应多个 Query，因此 Runner 要支持：

```text
context_id
```

和：

```text
reuse_context
```

正式评分时仍然保证 Case 独立。

但性能测试可以增加 Context Batch Mode：

```text
ingest once
query N times
```

两种模式要分开记录，不能混合比较。

***

# 29. 建议测试目录

```text
tests/
    sources/
        test_longmemeval.py
        test_locomo.py
        test_prefeval.py
        test_personamem.py
        test_memoryagentbench.py
        test_beam.py
        test_agentmembench.py

    dimensions/
        test_d01.py
        test_d02.py
        test_d03.py
        test_d04.py
        test_d05.py
        test_d06.py
        test_d07.py
        test_d08.py

    systems/
        test_reme.py

    integration/
        test_d01_reme.py
        test_d02_reme.py
        ...
```

***

# 30. 每个 Source Adapter 的最低测试要求

至少包含：

```text
test_load_raw
test_record_count
test_required_fields
test_unique_ids
test_normalize
test_source_traceability
test_context_reference
test_gold_reference
test_deterministic_output
```

已有三个 Adapter 额外增加：

```text
test_legacy_equivalence
```

避免迁移过程中破坏现有逻辑。

***

# 31. 固定随机抽样

所有 300 Case 的抽取必须固定 seed。

建议：

```text
selection_seed: 20260901
```

并将最终选中的：

```text
source_record_id
source_question_id
```

写入 manifest。

以后即使 Dataset Adapter 更新，v0.1 仍然可以完全复现。

***

# 32. v0.1 开发顺序

建议严格按照以下顺序推进。

## Step 1

确认本地已有三套数据：

```text
LongMemEval
LoCoMo
PersonaMem-v2
```

重点确认 LongMemEval 是否已经是 cleaned。

## Step 2

下载：

```text
PrefEval 三套
MemoryAgentBench Conflict Resolution
BEAM
BEAM-10M
AgentMemBench
```

## Step 3

运行 Dataset Audit。

此时不要修改 Benchmark Logic。

## Step 4

定义并冻结：

```text
Core Envelope v0.1
Canonical Event v0.1
八套 Gold Payload v0.1
```

## Step 5

迁移已有：

```text
LongMemEvalAdapter
LoCoMoAdapter
PersonaMemAdapter
```

先建立 regression fixture，再修改。

## Step 6

实现：

```text
PrefEvalAdapter
```

用它验证新的 SourceAdapter Interface。

## Step 7

实现：

```text
MemoryAgentBenchAdapter
```

验证一个 Context 多 Query。

## Step 8

实现：

```text
AgentMemBenchAdapter
```

验证 Event 和 Multi-user。

## Step 9

实现：

```text
BeamAdapter
```

最后处理复杂长 Context。

## Step 10

Source Adapter 全部通过以后，生成：

```text
datasets/staging/
```

## Step 11

依次实现：

```text
D01Builder
D02Builder
D03Builder
D04Builder
D05Builder
D06Builder
D07Builder
D08Builder
```

## Step 12

生成 300 Case：

```text
datasets/benchmark/v0_1/
```

## Step 13

执行 Benchmark Audit。

没有通过 Audit，不进入系统评测。

## Step 14

包装现有：

```text
ReMeAdapter
```

形成：

```text
ReMeSystemAdapter
```

## Step 15

先跑最成熟的：

```text
D02 LongMemEval
```

验证新架构没有破坏现有 ReMe LongMemEval 结果。

## Step 16

依次接入：

```text
D01
D03
D04
D05
D06
D08
D07
```

D07 最后跑，因为成本最高。

***

# 33. v0.1 完成标准

v0.1 不以高 Benchmark Score 作为完成标准。

只需要达到以下条件。

### 数据层

```text
7 套公开数据源全部固定版本
300 Case 构建成功
所有 Case 可以追溯到公开 Source
8 种 Gold Payload Schema 完整
Benchmark Audit 100% 通过
```

### Adapter 层

```text
7 个 Source Adapter
8 个 Dimension Builder
1 个 ReMe System Adapter
```

其中 LongMemEval、LoCoMo、PersonaMem-v2 必须以修改现有 Adapter 为主。

### 运行层

每个 Dimension 至少完成一次：

```text
Load
Ingest
Query 或 Inspect
Evaluate
Save Result
```

### 指标层

D01：

```text
Write Precision
Write Recall
```

D02：

```text
Hit@K
Recall@K
MRR
```

D03：

```text
Temporal Accuracy
Long-gap Recall
Deleted Hit Rate
```

D04：

```text
Activation Precision
Activation Recall
Utilization Rate
E2E Accuracy
```

D05：

```text
Profile Precision
Preference Recall
Profile Consistency
```

D06：

```text
Latest-value Accuracy
Conflict Resolution Accuracy
Stale Retrieval Rate
```

D07：

```text
Recall by Scale
Recall Degradation
P95 Retrieval Latency
Cost
```

其中严格 Recall Degradation 只有 paired scale group 才计算。

D08：

```text
Cross-user Leakage Rate
Deletion Completeness
Forbidden Canary Exposure Rate
```

***

# 34. 当前阶段最重要的工程约束

第一，不再增加公开数据集。

先把这 8 个维度的骨架彻底跑通。

第二，不强求所有原始 Dataset 字段一致。

统一的是 Benchmark Core Envelope，不是 Raw Dataset。

第三，Source Adapter 不写 Benchmark 策略。

它只负责忠实理解公开数据。

第四，所有采样、构造正负样本、生命周期、Scale Pair、Privacy Pair 都进入 Dimension Builder。

第五，System Adapter 永远不关心数据来自 LongMemEval、LoCoMo 还是 BEAM。

它只接收统一的：

```text
Context
Event
Query
Action
```

第六，已有代码优先做兼容升级。

尤其：

```text
LongMemEval
LoCoMo
PersonaMem-v2
ReMe
```

都不应该推倒重写。

第七，D01 Gold Memory 是第一版数据中最需要人工审核的部分。

LongMemEval 的 Evidence 不能直接等价成完整 Write Gold。

第八，D07 的 Recall Degradation 必须来自 Paired Scale Case。

不能直接比较不同 BEAM Conversation 的 100K 和 10M 得分，然后称为 Degradation。

第九，D04 必须同时有 Activation Positive 和 Negative。

否则无法识别系统是否无条件调用 Memory。

第十，整个 v0.1 的真正目标是获得一个稳定的：

```text
Raw Dataset
↓
Source Adapter
↓
Canonical Record
↓
Dimension Builder
↓
300 Benchmark Cases
↓
ReMe System Adapter
↓
8 Dimension Evaluation
```

完整闭环。

只要这个闭环稳定，后续从 300 Case 扩展到 3000 Case，主要工作就会变成抽样、Gold 标注和数据质量控制，而不是再次修改底层架构。
