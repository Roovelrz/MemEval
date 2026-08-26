# Memory Eval HTML 报告开发规范

## 1. 目标

基于现有 Eval 产物生成本地静态 HTML 报告，不修改 Eval Runner、Trace Analyzer 和原始 JSON/JSONL 结构。

整体链路固定为：

```text
Eval Runner
→ JSON / JSONL Artifacts
→ Trace Analyzer
→ trace_summary.json
→ HTML Reporter
→ 本地可交互 Eval Dashboard
```

HTML Reporter 只负责读取现有结果并渲染，不参与评测、打分或根因判定。

## 2. 字段展示原则

### 一级字段

一级导航、一级模块、一级指标必须使用中文描述，例如：

- 综合能力评分
- 工程健康度
- 检索质量
- 回答质量
- 有依据端到端能力
- 能力维度表现
- 失败归因
- 流程观测
- 性能与时延
- API 稳定性
- 版本对比
- Case 追踪
- 运行信息

### 二级与三级字段

二级、三级字段必须直接展示 `trace_summary.json`、`retrieval.jsonl`、`prepared.jsonl`、`answers.jsonl`、`scores.jsonl` 中已有的原始字段名。

禁止为了展示重新命名二级、三级字段。

示例：

```text
一级：
检索质量

二级：
hit_at_k
recall_at_k
mrr
first_evidence_rank
```

```text
一级：
回答阶段

二级：
success_rate
failure_rate
empty_answer_count
latency_ms

三级：
avg
p50
p95
p99
```

## 3. 页面结构

```text
report/
├── index.html
├── capabilities/
│   ├── knowledge-update.html
│   ├── multi-session.html
│   ├── single-session-assistant.html
│   ├── single-session-preference.html
│   ├── single-session-user.html
│   └── temporal-reasoning.html
├── pipeline/
│   ├── add.html
│   ├── index.html
│   ├── search.html
│   ├── answer.html
│   └── judge.html
├── failures/
│   ├── retrieval-miss.html
│   ├── retrieval-wrong-chunk.html
│   ├── answer-failure.html
│   └── judge-suspect.html
├── cases/
│   ├── index.html
│   └── <case_id>.html
├── performance/
│   ├── latency.html
│   ├── api-stability.html
│   └── token-usage.html
├── comparison/
│   └── index.html
├── run-info/
│   └── index.html
└── assets/
    ├── app.js
    └── style.css
```

# 4. 首页 Dashboard

## 一级指标：综合能力评分

一级标题：

```text
综合能力评分
```

展开后使用原始二级字段：

```text
hit_at_k
recall_at_k
mrr
answer_accuracy
grounded_end_to_end_accuracy
```

第一版展示性聚合建议：

```text
retrieval_quality
= recall_at_k × 60%
+ mrr × 40%

综合能力评分
= retrieval_quality × 40%
+ answer_accuracy × 20%
+ grounded_end_to_end_accuracy × 40%
```

必须注明这是本地 Eval 的展示性聚合指标，不修改原始 Trace 指标。

## 一级指标：工程健康度

一级标题：

```text
工程健康度
```

二级字段：

```text
pipeline_success_rate
add_success_rate
index_success_rate
search_success_rate
api_error_count
timeouts
retries
```

工程健康度和综合能力评分必须分开显示。

## 一级指标：检索质量

一级标题：

```text
检索质量
```

二级字段：

```text
hit_at_k
recall_at_k
mrr
full_evidence_recall_rate
partial_evidence_rate
zero_evidence_rate
```

如当前 run 固定 `top_k = 10`，同时展示：

```text
hit_at_10
recall_at_10
```

## 一级指标：回答质量

一级标题：

```text
回答质量
```

二级字段：

```text
answer_accuracy
answer_scored_cases
answer_failure_count
judge_wrong_count
```

## 一级指标：有依据端到端能力

一级标题：

```text
有依据端到端能力
```

二级字段：

```text
grounded_end_to_end_accuracy
quadrants
```

三级字段：

```text
A_retrieval_pass_answer_pass
B_retrieval_fail_answer_fail
C_retrieval_pass_answer_fail
D_retrieval_fail_answer_pass
not_scored
```

# 5. 一级模块：能力维度表现

一级标题：

```text
能力维度表现
```

数据源：

```text
question_type_breakdown
```

一级中文名称与原始类型映射：

| 一级中文名称 | 原始 question_type |
|---|---|
| 知识更新 | `knowledge-update` |
| 多会话推理 | `multi-session` |
| 单会话助手信息 | `single-session-assistant` |
| 单会话偏好 | `single-session-preference` |
| 单会话用户信息 | `single-session-user` |
| 时间推理 | `temporal-reasoning` |

每个能力卡片内部展示原始字段：

```text
case_count
hit_at_10
recall_at_10
mrr
accuracy
avg_search_latency_ms
```

点击能力卡片进入详情页。

# 6. 能力详情页

例如：

```text
capabilities/multi-session.html
```

一级标题：

```text
多会话推理
```

顶部字段：

```text
case_count
hit_at_10
recall_at_10
mrr
accuracy
avg_search_latency_ms
```

Case 表格：

```text
case_id
hit_at_k
recall_at_k
mrr
first_evidence_rank
answer_correct
judge_label
quadrant
root_cause
```

点击 `case_id` 进入 Case Trace。

# 7. 一级模块：失败归因

一级标题：

```text
失败归因
```

数据源：

```text
root_cause_distribution
```

二级字段：

```text
PASS
DATA_ERROR
ADD_FAILURE
INDEX_FAILURE
RETRIEVAL_MISS
RETRIEVAL_PARTIAL
RETRIEVAL_LOW_RANK
RETRIEVAL_WRONG_CHUNK
CONTEXT_LOSS
CONTEXT_TRUNCATION
ANSWER_FAILURE
JUDGE_SUSPECT
API_FAILURE
TIMEOUT
PIPELINE_FAILURE
```

首页重点显示非零失败项。

点击 Root Cause 进入失败 Case 列表页。

失败列表字段：

```text
case_id
question_type
hit_at_k
recall_at_k
mrr
first_evidence_rank
answer_correct
judge_label
quadrant
root_cause
explanation
```

# 8. 一级模块：流程观测

一级导航：

```text
流程观测
```

包含：

- 写入阶段
- 索引阶段
- 检索阶段
- 回答阶段
- 判分阶段

## 写入阶段

一级标题：

```text
写入阶段
```

二级字段：

```text
add_success_rate
added_sessions
failed_add_sessions
added_turns
evidence_add_success_rate
duplicate_add_count
empty_content_add_count
add_latency_ms
```

三级字段：

```text
avg
p50
p95
p99
```

## 索引阶段

一级标题：

```text
索引阶段
```

二级字段：

```text
index_success_rate
indexed_document_count
indexed_chunk_count
index_latency_ms
```

三级字段：

```text
avg
p50
p95
p99
```

## 检索阶段

一级标题：

```text
检索阶段
```

二级字段：

```text
search_success_rate
search_request_count
empty_search_result_count
search_retry_count
search_latency_ms
hit_at_10
recall_at_10
mrr
full_evidence_recall_rate
partial_evidence_rate
zero_evidence_rate
```

三级字段：

```text
avg
p50
p95
p99
```

## 回答阶段

一级标题：

```text
回答阶段
```

数据源：

```text
answer_stage
```

二级字段：

```text
requested_rows
successful_rows
failed_rows
success_rate
failure_rate
empty_answer_count
timeout_count
api_request_count
retry_count
latency_ms
token_usage
model
prompt_version
prompt_template_sha256
```

三级字段：

```text
latency_ms.avg
latency_ms.p50
latency_ms.p95
latency_ms.p99
token_usage.input_tokens
token_usage.output_tokens
token_usage.total_tokens
token_usage.cost
```

## 判分阶段

一级标题：

```text
判分阶段
```

数据源：

```text
judge_stage
```

二级字段：

```text
requested_rows
successful_rows
failed_rows
correct_rows
accuracy
success_rate
failure_rate
correct_count
wrong_count
parse_failure_count
timeout_count
api_request_count
retry_count
latency_ms
token_usage
model
prompt_version
prompt_template_sha256
human_review_count
judge_human_disagreement_rate
```

# 9. 一级模块：性能与时延

一级标题：

```text
性能与时延
```

数据源：

```text
latency_breakdown
```

二级字段：

```text
Add
Index
Search
Answer
Judge
```

三级字段：

```text
avg
p50
p95
p99
```

# 10. 一级模块：API 稳定性

一级标题：

```text
API 稳定性
```

数据源：

```text
api_stability
```

二级、三级字段保持原始名称。

Memory：

```text
memory
  memory_add_requests
  memory_index_requests
  memory_search_requests
  http_2xx
  http_4xx
  http_5xx
  timeouts
  retries
```

Answer / Judge：

```text
answer_api_requests
judge_api_requests
answer_retries
judge_retries
timeouts
api_error_count
```

# 11. 一级模块：证据数量表现

一级标题：

```text
证据数量表现
```

数据源：

```text
evidence_count_breakdown
```

二级字段：

```text
single_evidence
multiple_evidence
```

三级字段：

```text
case_count
recall_at_10
accuracy
```

# 12. 一级模块：Case 追踪

一级标题：

```text
Case 追踪
```

列表页字段：

```text
case_id
question_type
hit_at_k
recall_at_k
mrr
first_evidence_rank
answer_correct
judge_label
quadrant
root_cause
explanation
```

支持筛选：

```text
question_type
root_cause
answer_correct
judge_label
```

默认失败 Case 排在前面。

# 13. Case Trace 详情页

## 一级模块：数据输入

一级标题：

```text
数据输入
```

二级字段：

```text
case_id
question_type
question
gold_answer
evidence_session_ids
total_sessions
```

## 一级模块：写入追踪

一级标题：

```text
写入追踪
```

二级字段：

```text
expected_sessions
added_sessions
expected_evidence_sessions
added_evidence_sessions
failed_session_ids
duplicate_session_ids
namespace
workspace
add_latency_ms
status
```

不存在的字段统一显示：

```text
NOT_RECORDED
```

## 一级模块：检索追踪

一级标题：

```text
检索追踪
```

二级字段：

```text
query
top_k
hit_at_k
recall_at_k
mrr
first_evidence_rank
gold_evidence_count
retrieved_evidence_count
missing_evidence_ids
best_evidence_score
best_non_evidence_score
evidence_score_gap
evidence_content_present
```

TopK 三级字段：

```text
rank
session_id
score
is_evidence
timestamp
text
```

Evidence 项必须视觉突出。

## 一级模块：回答追踪

一级标题：

```text
回答追踪
```

二级字段：

```text
retrieved_context
context_count
context_total_length
context_total_tokens
evidence_in_retrieved_context
evidence_in_answer_prompt
truncated
evidence_after_truncation
generated_answer
gold_answer
```

## 一级模块：判分追踪

一级标题：

```text
判分追踪
```

二级字段：

```text
generated_answer
gold_answer
judge_raw_response
parsed_label
judge_label
is_correct
human_review
```

## 一级模块：问题诊断

一级标题：

```text
问题诊断
```

二级字段：

```text
quadrant
root_cause
explanation
```

`root_cause != PASS` 时必须明显展示。

# 14. 一级模块：版本对比

一级标题：

```text
版本对比
```

数据源：

```text
comparison
```

二级字段：

```text
baseline_run
shared_case_count
metric_deltas
root_cause_deltas
newly_fixed_cases
newly_failed_cases
comparison_notes
```

三级字段直接使用现有 Trace 原始字段。

`metric_deltas`：

```text
hit_at_10
recall_at_10
mrr
accuracy
add_p95_ms
search_p95_ms
answer_p95_ms
judge_p95_ms
error_rate
total_tokens
cost
```

`root_cause_deltas`：

```text
PASS
DATA_ERROR
ADD_FAILURE
INDEX_FAILURE
RETRIEVAL_MISS
RETRIEVAL_PARTIAL
RETRIEVAL_LOW_RANK
RETRIEVAL_WRONG_CHUNK
CONTEXT_LOSS
CONTEXT_TRUNCATION
ANSWER_FAILURE
JUDGE_SUSPECT
API_FAILURE
TIMEOUT
PIPELINE_FAILURE
```

`newly_fixed_cases` 和 `newly_failed_cases` 必须支持跳转 Case Trace。

# 15. 一级模块：运行信息

一级标题：

```text
运行信息
```

数据源：

```text
run_info
version_fixed_fields
observability_gaps
conclusions
```

二级字段：

```text
run_id
dataset_name
dataset_version
case_count
session_count
turn_count
evidence_session_count
memory_backend
memory_version
top_k
answer_model
judge_model
answer_prompt_version
judge_prompt_version
eval_code_commit
eval_code_dirty
start_time
end_time


```
# 15.1 四象限交互分析图
这个功能建议直接加入 HTML Dashboard，因为它和现在的 `quadrant` 分析天然对应。现在已经有：

```text
Retrieval Result
+
Answer Result
+
Grounded E2E
```

所以四象限图实际上是一个非常好的开发侧诊断入口。

---

# 新增功能：四象限交互分析图

## 一级模块名称

```text
端到端能力四象限分析
```

页面：

```text
analysis/quadrant.html
```

或者直接放首页：

```text
综合能力评分
    ↓
四象限分析
```

---

# 一、四象限定义

横轴：

```text
Retrieval
```

纵轴：

```text
Answer
```

形成：

```
                 Answer PASS
                      ↑

        B区                 A区

 Retrieval FAIL       Retrieval PASS
 Answer FAIL          Answer PASS


        D区                 C区

 Retrieval FAIL       Retrieval PASS
 Answer PASS          Answer FAIL


                      ↓
                 Answer FAIL
```

实际对应：

| 区域 | 名称       | 含义                      |
| -- | -------- | ----------------------- |
| A  | 完美通过     | Memory 找到了正确证据，并回答正确    |
| B  | 双失败      | Memory 没找到，回答也失败        |
| C  | 检索成功回答失败 | Memory 有能力，但生成阶段有问题     |
| D  | 检索失败回答成功 | 可能依赖模型自身知识，Memory 没发挥作用 |

对应 Trace 字段：

```text
quadrant
```

例如：

```json
{
  "quadrant": "A_retrieval_pass_answer_pass"
}
```

---

# 二、交互图展示形式

建议：

散点图。

每一个点代表：

```text
一个 Case
```

例如：

```
              Answer Accuracy

                    ↑

        ●case01          ●case05



 Retrieval →
```

点的信息：

鼠标 hover：

显示：

```text
case_id

question_type

root_cause

hit_at_10

recall_at_10

answer_correct

judge_label
```

点击：

直接跳转：

```text
cases/<case_id>.html
```

---

# 三、不同粒度查看

这个图不要只支持 Case。

建议支持三个粒度切换：

## Level 1：Case 级别

默认。

一个点：

```text
一个 case
```

用途：

定位 Bad Case。

例如：

发现：

```
C区大量聚集
```

说明：

Retrieval 没问题，但是 Answer 有问题。

---

## Level 2：Question Type 级别

一个点：

```text
一种能力类型
```

例如：

```
multi-session

single-session-preference
```

计算：

该类型所有 Case 的平均值。

例如：

```
Multi Session

Retrieval:
100%

Answer:
50%
```

落在：

C区域附近。

说明：

多会话 Memory 找得到，但是推理能力不足。

---

## Level 3：Run 级别

一个点：

```text
一次完整实验
```

用于：

ReMe

vs

Mnemosyne

vs

内部 Memory

例如：

```
ReMe

Retrieval:
95

Answer:
70


Mnemosyne

Retrieval:
80

Answer:
65
```

用于横向比较。

---

# 四、加入 MD 规范补充

给 Codex 增加：

```markdown
# 新增模块：端到端能力四象限分析

## 页面

analysis/quadrant.html


## 功能

根据 retrieval 和 answer 两个维度生成交互式四象限散点图。


## 数据粒度

支持：

- Case
- Question Type
- Run


## 默认模式

Case


## X轴

Retrieval


来源字段：

hit_at_k
recall_at_k
first_evidence_rank


## Y轴

Answer


来源字段：

answer_correct
judge_label


## 象限字段

使用：

quadrant


映射：

A_retrieval_pass_answer_pass

B_retrieval_fail_answer_fail

C_retrieval_pass_answer_fail

D_retrieval_fail_answer_pass


## 点击行为

点击任意点：

跳转：

cases/<case_id>.html


## Hover展示

必须显示：

case_id

question_type

root_cause

hit_at_k

recall_at_k

mrr

answer_correct

judge_label


## 过滤

支持：

question_type

root_cause

quadrant

answer_correct

judge_label


## 颜色规则

按照 quadrant 区分。

禁止改变 quadrant 定义。
```

---

# 五、Memory Eval 数据层级关系

你现在确实需要把这个概念理顺。

Memory Eval 的数据不是平铺的，而是树状结构。

从大到小：

```
Run
│
├── Dataset
│
├── Case
│
├── Session
│
├── Turn
│
├── Block / Chunk
│
└── Evidence
```

---

## 1. Run

最大一次实验。

例如：

```
Run_20260826_ReMe_LongMemEval20
```

表示：

一次完整测试。

里面包含：

* 使用哪个 Memory
* 使用哪个 Dataset
* 使用哪个模型
* 参数配置

例如：

```text
Memory:
ReMe

Dataset:
LongMemEval-ZH

Case:
20
```

---

## 2. Dataset

数据集。

例如：

```
LongMemEval
```

里面有很多 Case。

---

## 3. Case

核心评测单位。

你现在最重要的对象。

一个 Case 对应：

```
一个问题
+
一段完整历史记忆
+
一个标准答案
```

例如：

用户问：

```
我去年在哪里买过电脑？
```

背后有：

几十个历史 session。

Case 就是完整的一题。

---

## 4. Session

Case 内部的对话轮次集合。

例如：

Case：

```
用户寻找购买记录
```

历史：

Session 1：

```
2025-01-01
讨论电脑配置
```

Session 2：

```
2025-03-05
购买电脑
```

Session 3：

```
2025-05-01
评价电脑
```

所以：

```
Case
=
多个 Session
```

---

## 5. Turn

Session 内的一轮消息。

例如：

Session：

```
用户：我想买电脑

助手：预算多少？

用户：5000左右

助手：推荐...
```

拆开：

```
Turn 1
用户

Turn 2
助手

Turn 3
用户

Turn 4
助手
```

所以：

```
Session
=
多个 Turn
```

---

## 6. Block / Chunk

为了 Memory 存储和 Retrieval。

Turn 进一步切分。

例如：

一个长 Turn：

```
我去年三月份在成都买了一台MacBook Air M2，
当时花了8500元，因为主要用于机器学习开发...
```

可能拆：

```
Block 1:
购买时间

Block 2:
购买地点

Block 3:
价格

Block 4:
用途
```

所以：

```
Turn
=
多个 Block
```

---

## 7. Evidence

最关键。

不是所有 Block 都有用。

只有支持答案的部分：

```
Evidence
```

例如：

问题：

```
电脑多少钱买的？
```

历史：

Block:

```
2025年3月成都购买MacBook Air M2
```

不是 Evidence。

Block:

```
支付8500元
```

才是 Evidence。

所以：

```
Block
包含
Evidence
```

---

# 六、对应到你的 10095 block

你的统计：

```
20 Case

↓

964 Session

↓

10055 Turn

↓

10095 Block
```

这是正确的。

不是：

```
10095 Session
```

而是：

```
20个评测问题

每个问题包含大量历史对话

历史对话拆成 Session

Session拆成Turn

Turn拆成Block

其中部分Block组成Evidence
```

你的数据关系：

```
LongMemEval-ZH-20

        |
        |
      20 Case

        |
        |
     964 Session

        |
        |
    10055 Turn

        |
        |
   10095 Block

        |
        |
 Evidence Block
```

---

# 七、开发侧最应该关注的层级

实际 Debug 顺序：

## 第一层：Case

发现：

```
Case失败
```

↓

## 第二层：Quadrant

判断：

```
属于哪个象限？
```

↓

## 第三层：Session

看：

```
有没有找到正确历史
```

↓

## 第四层：Block

看：

```
为什么 Chunk 没命中
```

↓

## 第五层：Answer Context

看：

```
正确证据有没有进入 Prompt
```

↓

## 第六层：Answer

看：

```
LLM为什么回答错误
```

---

所以你现在的 HTML Dashboard 最核心的链路应该是：

```
四象限图
      ↓
Case
      ↓
Session
      ↓
Turn
      ↓
Block
      ↓
Evidence
      ↓
Answer Context
      ↓
LLM Answer
```

这套结构基本就是一个 Memory Eval 平台的核心形态。你现在已有 Trace 数据，只差把这些层级通过 UI 串起来。



# 16. 首页推荐布局

从上到下：

```text
第一屏
综合能力评分
工程健康度
检索质量
回答质量
有依据端到端能力

第二屏
能力维度表现

第三屏
失败归因

第四屏
流程观测

第五屏
性能与时延

第六屏
API 稳定性

第七屏
版本对比

第八屏
重点 Bad Case
```

# 17. 重点 Bad Case

一级标题：

```text
重点 Bad Case
```

优先级：

```text
PIPELINE_FAILURE
API_FAILURE
ADD_FAILURE
INDEX_FAILURE
RETRIEVAL_MISS
RETRIEVAL_WRONG_CHUNK
RETRIEVAL_PARTIAL
CONTEXT_LOSS
CONTEXT_TRUNCATION
ANSWER_FAILURE
JUDGE_SUSPECT
PASS
```

字段：

```text
case_id
question_type
root_cause
answer_correct
```

点击进入 Trace。

# 18. 视觉与实现要求

第一版建议：

```text
Python
Jinja2
HTML
CSS
少量原生 JavaScript
```

要求：

- 本地静态生成
- 不依赖数据库
- 不依赖 Node.js 构建链
- 支持双击打开
- 必要时支持 `python -m http.server`
- 所有页面使用相对路径
- Case 表格支持筛选
- PASS 与失败状态视觉区分
- Evidence 在 TopK 中视觉突出
- 百分比与小数显示规则统一
- 一级中文标签固定
- 二级、三级字段不做中文翻译

# 19. Reporter 输入

优先读取：

```text
<run_dir>/
├── run_config.json
├── dataset_manifest.json
├── add_trace.jsonl
├── retrieval.jsonl
├── prepared.jsonl
├── answers.jsonl
├── scores.jsonl
├── api_errors.jsonl
├── failures.jsonl
├── summary.json
├── trace_summary.json
└── trace/
```

`trace_summary.json` 作为首页和聚合页主数据源。

Case 详情按需关联：

```text
retrieval.jsonl
prepared.jsonl
answers.jsonl
scores.jsonl
add_trace.jsonl
```

禁止修改源文件。

# 20. Reporter 输出

统一输出：

```text
<run_dir>/report/
```

至少生成：

```text
report/index.html
report/cases/index.html
report/cases/<case_id>.html
report/capabilities/*.html
report/pipeline/*.html
report/failures/*.html
report/performance/*.html
report/comparison/index.html
report/run-info/index.html
report/assets/style.css
report/assets/app.js
```

# 21. 开发约束

- HTML Reporter 不参与 Eval 计算
- 不修改原始 JSON/JSONL
- 一级名称使用本文定义的中文
- 二级、三级字段只使用现有 Trace 原始字段名
- 缺失字段统一显示 `NOT_RECORDED`
- 禁止 HTML 层重新判定 `root_cause`
- 禁止 HTML 层重新计算 Answer/Judge 结果
- 综合能力评分仅为展示性聚合指标
- 原始指标始终可追溯
- 所有 Case ID 可点击进入完整 Trace
- 所有失败类型可筛选到对应 Case
- 所有能力维度可追溯到对应 Case
- 所有版本变化可追溯到具体 Case

# 22. 最终验收

- [ ] 双击 `report/index.html` 可打开
- [ ] 首页显示综合能力评分
- [ ] 首页显示工程健康度
- [ ] 首页显示检索质量
- [ ] 首页显示回答质量
- [ ] 首页显示有依据端到端能力
- [ ] 能力维度表现可点击
- [ ] 失败归因可点击
- [ ] 所有 Case 可进入 Trace
- [ ] Trace 可看到 Dataset → Add → Retrieval → Answer → Judge → Diagnosis
- [ ] Evidence 在 TopK 中有明显标记
- [ ] 可查看 `root_cause`
- [ ] 可查看 `explanation`
- [ ] 可查看各阶段 latency
- [ ] 可查看 API 稳定性
- [ ] 可查看 token usage
- [ ] 可查看版本对比
- [ ] `newly_fixed_cases` 可跳 Case Trace
- [ ] `newly_failed_cases` 可跳 Case Trace
- [ ] 缺失字段显示 `NOT_RECORDED`
- [ ] Reporter 不修改任何原始 Eval 产物
