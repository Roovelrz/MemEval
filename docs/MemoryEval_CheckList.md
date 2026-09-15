# Memory Eval 查看方法清单

> 本清单适用于当前 MemEval-v0.1 链路（`scripts/run_memeval.py`）与历史
> LongMemEval 链路。MemEval 专属的新增检查项见第 6.1、12.1、20.1 节；
> 各维度指标语义见 `dataset/MemEval-v0.1/dimensions/*/v0.1/README.md`。

## 1. Run 基础信息

- [ ] run_id
- [ ] dataset_name
- [ ] dataset_version
- [ ] case_count
- [ ] session_count
- [ ] turn_count
- [ ] evidence_session_count
- [ ] memory_backend
- [ ] memory_version
- [ ] top_k
- [ ] answer_model
- [ ] judge_model
- [ ] prompt_version
- [ ] eval_code_commit
- [ ] start_time
- [ ] end_time

## 2. Dataset 完整性

- [ ] 实际加载 case 数
- [ ] 实际加载 session 数
- [ ] 实际加载 turn 数
- [ ] evidence session 数
- [ ] 缺失 question 数
- [ ] 缺失 gold answer 数
- [ ] 缺失 evidence ID 数
- [ ] session_id 重复数
- [ ] case_id 重复数
- [ ] 时间戳异常数
- [ ] 数据解析失败数
- [ ] 数据跳过数

## 3. Add 写入观测

### 全局指标

- [ ] Add Success Rate
- [ ] Add Failure Rate
- [ ] 成功写入 session 数
- [ ] 失败写入 session 数
- [ ] 成功写入 turn 数
- [ ] evidence session 写入成功率
- [ ] 重复写入数
- [ ] 空内容写入数
- [ ] Add 平均耗时
- [ ] Add P50
- [ ] Add P95
- [ ] Add P99
- [ ] 单 case 总写入耗时

### 单 Case Trace

- [ ] expected_sessions
- [ ] added_sessions
- [ ] expected_evidence_sessions
- [ ] added_evidence_sessions
- [ ] failed_session_ids
- [ ] duplicate_session_ids
- [ ] namespace
- [ ] user_id
- [ ] workspace
- [ ] Add error
- [ ] Add status

## 4. Index / Memory Processing 观测

- [ ] Index Success Rate
- [ ] Index Failure Rate
- [ ] Index 总耗时
- [ ] Index P50
- [ ] Index P95
- [ ] Index P99
- [ ] 实际索引文档数
- [ ] 实际索引 chunk 数
- [ ] 平均 chunk 数 / session
- [ ] 空 chunk 数
- [ ] chunk 失败数
- [ ] embedding 调用数
- [ ] embedding 失败数
- [ ] extraction 调用数
- [ ] extraction 失败数
- [ ] memory 写入前后数量变化
- [ ] 被过滤 memory 数
- [ ] 被合并 memory 数
- [ ] 被更新 memory 数

## 5. Search 请求观测

- [ ] Search Success Rate
- [ ] Search Failure Rate
- [ ] Search 请求总数
- [ ] query
- [ ] top_k
- [ ] 实际返回数量
- [ ] 空结果数
- [ ] Search 平均耗时
- [ ] Search P50
- [ ] Search P95
- [ ] Search P99
- [ ] timeout 数
- [ ] retry 数
- [ ] Search error type
- [ ] Search error message

## 6. Retrieval 核心指标

- [ ] Hit@1
- [ ] Hit@3
- [ ] Hit@5
- [ ] Hit@10
- [ ] Recall@1
- [ ] Recall@3
- [ ] Recall@5
- [ ] Recall@10
- [ ] Precision@K
- [ ] MRR
- [ ] First Evidence Rank
- [ ] Mean Evidence Rank
- [ ] Retrieved Evidence Count
- [ ] Total Evidence Count
- [ ] Missing Evidence Count
- [ ] Missing Evidence IDs
- [ ] Full Evidence Recall Rate
- [ ] Partial Evidence Rate
- [ ] Zero Evidence Rate

## 6.1 MemEval 维度专属检索指标

- [ ] D02 metrics_by_k（主指标 K=3，其余 K 悬停查看）
- [ ] D05 needle_recall_at_k（profile 证据事件文本命中；session 级仅参照）
- [ ] D07 needle_recall_at_k（证据事件文本命中；session 级仅参照）
- [ ] D06 winning_fact_recall（冲突对最新事实召回）
- [ ] D06 stale_retrieval_rate（陈旧版本被返回比例，越低越好）
- [ ] D03 deleted_hit_rate（删除后陈旧残留暴露）
- [ ] 无记忆对照（--memory-adapter off）下检索指标如实为 0 而非 NOT_RECORDED

## 7. Retrieval 排序质量

- [ ] Best Evidence Score
- [ ] Best Non-Evidence Score
- [ ] Evidence Score Gap
- [ ] Evidence Average Score
- [ ] Non-Evidence Average Score
- [ ] Top1 是否 evidence
- [ ] Top3 evidence 数
- [ ] Top5 evidence 数
- [ ] Top10 evidence 数
- [ ] evidence 是否被排在大量 distractor 后
- [ ] evidence_content_present
- [ ] session 命中但 evidence turn 未返回的数量
- [ ] 重复 session 返回数
- [ ] 重复 chunk 返回数

## 8. Retrieval 按类型拆分

- [ ] Information Extraction Hit@K
- [ ] Multi-Session Reasoning Hit@K
- [ ] Knowledge Update Hit@K
- [ ] Temporal Reasoning Hit@K
- [ ] Abstention Accuracy
- [ ] 各 question_type Recall@K
- [ ] 各 question_type MRR
- [ ] 各 question_type 平均 Search Latency
- [ ] 单 evidence case 表现
- [ ] 多 evidence case 表现
- [ ] 不同 session 数量区间表现
- [ ] 不同历史长度区间表现

## 9. Answer 输入观测

- [ ] Answer Prompt Version
- [ ] Answer Model
- [ ] Question
- [ ] Retrieved Context 数量
- [ ] Retrieved Context 总字符数
- [ ] Retrieved Context 总 token 数
- [ ] Evidence 是否进入 retrieved_context
- [ ] Evidence 是否进入最终 prompt
- [ ] Prompt 是否发生截断
- [ ] 截断前 token 数
- [ ] 截断后 token 数
- [ ] 截断前 evidence 是否存在
- [ ] 截断后 evidence 是否存在
- [ ] Context 顺序
- [ ] Evidence 在 Context 中的位置
- [ ] distractor 数量

## 10. Answer 输出指标

- [ ] Answer Success Rate
- [ ] Answer Failure Rate
- [ ] Generated Answer
- [ ] Gold Answer
- [ ] Answer Empty Rate
- [ ] Answer Timeout Rate
- [ ] Answer Retry Count
- [ ] Answer 平均耗时
- [ ] Answer P50
- [ ] Answer P95
- [ ] Answer P99
- [ ] Answer Input Tokens
- [ ] Answer Output Tokens
- [ ] Answer Total Tokens
- [ ] Answer Cost

## 11. Judge 观测

- [ ] Judge Model
- [ ] Judge Prompt Version
- [ ] Judge Success Rate
- [ ] Judge Failure Rate
- [ ] Judge Raw Response
- [ ] Parsed Label
- [ ] CORRECT 数
- [ ] WRONG 数
- [ ] Judge Parse Failure 数
- [ ] Judge Timeout 数
- [ ] Judge Retry 数
- [ ] Judge 平均耗时
- [ ] Judge P50
- [ ] Judge P95
- [ ] Judge P99
- [ ] Judge Input Tokens
- [ ] Judge Output Tokens
- [ ] Judge Cost
- [ ] Human Review Result
- [ ] Judge / Human Disagreement Rate

## 12. End-to-End 核心指标

- [ ] Answer Accuracy
- [ ] Pipeline Success Rate
- [ ] Pipeline Failure Rate
- [ ] Retrieval PASS + Answer PASS 数
- [ ] Retrieval FAIL + Answer FAIL 数
- [ ] Retrieval PASS + Answer FAIL 数
- [ ] Retrieval FAIL + Answer PASS 数
- [ ] 有 evidence 时 Answer Accuracy
- [ ] 无 evidence 时 Answer Accuracy
- [ ] Full Evidence Recall 时 Answer Accuracy
- [ ] Partial Evidence 时 Answer Accuracy
- [ ] Zero Evidence 时 Answer Accuracy

## 12.1 MemEval 维度专属端到端指标

- [ ] D01 memory_recall / memory_precision（写入覆盖 Gold 证据；无写入时为 None）
- [ ] D05 personalized_answer_accuracy（依据偏好作答）
- [ ] D08 allowed_recall（允许记忆的召回义务）
- [ ] D08 forbidden_exposure / deleted_exposure_count / Canary 命中
- [ ] D08 effective_privacy_pass（无泄露 且 allowed_recall>0，防空检索刷分）
- [ ] D04 unsupported 状态保留（不折算为零分）

## 13. Root Cause 分类

- [ ] PASS
- [ ] DATA_ERROR
- [ ] ADD_FAILURE
- [ ] INDEX_FAILURE
- [ ] RETRIEVAL_MISS
- [ ] RETRIEVAL_PARTIAL
- [ ] RETRIEVAL_LOW_RANK
- [ ] RETRIEVAL_WRONG_CHUNK
- [ ] CONTEXT_LOSS
- [ ] CONTEXT_TRUNCATION
- [ ] ANSWER_FAILURE
- [ ] JUDGE_SUSPECT
- [ ] API_FAILURE
- [ ] TIMEOUT
- [ ] PIPELINE_FAILURE

## 14. 每个失败 Case 必查

- [ ] 原始 question
- [ ] gold answer
- [ ] gold evidence IDs
- [ ] evidence 是否成功 Add
- [ ] Search query 是否正确
- [ ] TopK 全部结果
- [ ] evidence 首次出现 rank
- [ ] evidence score
- [ ] distractor score
- [ ] missing evidence IDs
- [ ] returned text 是否真的包含 evidence
- [ ] evidence 是否进入 Answer Context
- [ ] evidence 是否被截断
- [ ] generated answer
- [ ] judge raw response
- [ ] parsed label
- [ ] root cause
- [ ] 修复建议

## 15. API 与系统稳定性指标

### Memory API

- [ ] Add 请求数
- [ ] Search 请求数
- [ ] HTTP 2xx 数
- [ ] HTTP 4xx 数
- [ ] HTTP 5xx 数
- [ ] timeout 数
- [ ] retry 数
- [ ] connection error 数
- [ ] rate limit 数
- [ ] 平均响应时间
- [ ] P95 响应时间
- [ ] P99 响应时间

### LLM API

- [ ] Answer API 请求数
- [ ] Judge API 请求数
- [ ] timeout
- [ ] retry
- [ ] rate limit
- [ ] server error
- [ ] token usage
- [ ] cost
- [ ] 平均 latency
- [ ] P95 latency
- [ ] P99 latency

## 16. 开发侧最需要看的 Dashboard

### 第一屏

- [ ] Run 状态
- [ ] Cases
- [ ] Pipeline Success Rate
- [ ] Add Success Rate
- [ ] Search Success Rate
- [ ] Hit@10
- [ ] Recall@10
- [ ] MRR
- [ ] Answer Accuracy
- [ ] End-to-End Accuracy

### 第二屏

- [ ] Add P95
- [ ] Search P95
- [ ] Answer P95
- [ ] Judge P95
- [ ] End-to-End P95
- [ ] timeout rate
- [ ] retry rate
- [ ] API error rate

### 第三屏

- [ ] Root Cause Distribution
- [ ] Retrieval Miss 数
- [ ] Partial Retrieval 数
- [ ] Context Loss 数
- [ ] Answer Failure 数
- [ ] Judge Suspect 数
- [ ] Pipeline Failure 数

### 第四屏

- [ ] question_type × Hit@10
- [ ] question_type × Recall@10
- [ ] question_type × Accuracy
- [ ] history length × Recall@10
- [ ] evidence count × Recall@10
- [ ] First Evidence Rank 分布

## 17. 单 Case Trace 页面

- [ ] Case ID
- [ ] Question Type
- [ ] Question
- [ ] Gold Answer
- [ ] Evidence IDs
- [ ] Add Status
- [ ] Added Sessions
- [ ] Search Query
- [ ] TopK
- [ ] Hit@K
- [ ] Recall@K
- [ ] MRR
- [ ] First Evidence Rank
- [ ] TopK Result List
- [ ] Evidence 标记
- [ ] Score
- [ ] Returned Text
- [ ] Answer Context
- [ ] Generated Answer
- [ ] Judge Result
- [ ] Root Cause
- [ ] Error Message
- [ ] Latency Breakdown

## 18. 每次 Run 必须保存的文件

- [ ] `run_config.json`
- [ ] `dataset_manifest.json`
- [ ] `add_trace.jsonl`
- [ ] `retrieval.jsonl`
- [ ] `prepared.jsonl`
- [ ] `answers.jsonl`
- [ ] `scores.jsonl`
- [ ] `api_errors.jsonl`
- [ ] `failures.jsonl`
- [ ] `summary.json`
- [ ] `trace_summary.json`
- [ ] `trace_summary.md`
- [ ] `trace_index.md`
- [ ] `judge_review.md`
- [ ] `cases/<case_id>.md`

## 18.1 MemEval Run 额外保存

- [ ] `results.jsonl`（逐 case 全量结果，含 retrieved_memories 与 metrics）
- [ ] `retrieval_run_config.json`（含 memory_adapter / top_k / selected_case_ids）
- [ ] `run_summary.json`（按维度汇总）
- [ ] `eval_code_snapshot/manifest.json`（实际运行代码快照）

## 19. 开发侧版本对比必须固定

- [ ] Dataset Version
- [ ] Case Selection
- [ ] Memory Adapter（reme / off）
- [ ] TopK
- [ ] Answer Model
- [ ] Judge Model
- [ ] Prompt Version
- [ ] Eval Code Version
- [ ] Memory Config
- [ ] Memory Version

消融实验额外固定：Judge 不变，仅切换 Answer 模型或 memory adapter；
各 arm 使用同一冻结 case 集合。

对比版本时重点查看：

- [ ] Hit@10 Δ
- [ ] Recall@10 Δ
- [ ] MRR Δ
- [ ] Accuracy Δ
- [ ] Add P95 Δ
- [ ] Search P95 Δ
- [ ] Error Rate Δ
- [ ] Cost Δ
- [ ] Root Cause Distribution Δ
- [ ] Regression Cases
- [ ] Newly Fixed Cases
- [ ] Newly Failed Cases

## 20. 最终开发侧结论必须回答

- [ ] Memory 是否全部成功写入
- [ ] Evidence 是否全部进入 Memory
- [ ] Search 是否能稳定找到 Evidence
- [ ] 主要问题是 Recall 还是 Ranking
- [ ] 多 Evidence 场景是否明显更差
- [ ] Temporal 场景是否明显更差
- [ ] Knowledge Update 场景是否明显更差
- [ ] Evidence 找到后 Answer 是否还能正确回答
- [ ] 是否存在 Context 丢失
- [ ] 是否存在 Judge 误判
- [ ] 最大耗时位于哪一层
- [ ] 最大错误来源位于哪一层
- [ ] 当前版本相对上一版本改善了什么
- [ ] 当前版本相对上一版本退化了什么