# Trace 汇总报告

> 评测目录：`E:\LRZ_Workplace\fork\memory_eval_pipeline\results\en_full\reme\reme-longmemeval-en-20-v1\Detailed Trace Report`  
> 排查原则：始终沿真实链路从上游向下检查——Add → Retrieval → Context → Answer → Judge。

## Run 基础信息

| 字段 | 值 |
| --- | --- |
| Run ID | `reme-longmemeval-en-20-v1` |
| Dataset | LongMemEval 英文全量基准 / `local-d6f21ea9` |
| Case / Session / Turn / Evidence Session | 20 / 980 / 10135 / 20 |
| Memory | ReMe `0.4.1.8` |
| TopK | 10 |
| Answer / Judge Model | `deepseek-v4-flash` / `deepseek-v4-flash` |
| Prompt Version | `longmemeval-answer-v2-structured-time` / `longmemeval-judge-v1` |
| Eval Commit | `fb4123b6225ea289cf2014d52ad1b07da2bc09d2`（dirty=True） |
| Eval Code Snapshot | `4c8f717eed3abc17b90df208c3b5248906ab24f65abd4c6ddf1e64d503c0ddea` |
| Reproducibility | `PASS_DIRTY_WITH_SOURCE_SNAPSHOT` |
| Start / End | 2026-08-26T08:13:05.387547+00:00 / 2026-08-26T08:17:02.483113+00:00 |

## Dataset 完整性

- Run 选中数据验收状态：**PASS_WITH_WARNINGS**；源数据验收状态：**NOT_RECORDED**。

| 指标 | 数量 |
| --- | ---: |
| 实际加载 Case / Session / Turn / Evidence Session | 20 / 980 / 10135 / 20 |
| 缺失 Question / Gold Answer / Evidence ID | 0 / 0 / 0 |
| 重复 Session ID / Case ID | 2 / 0 |
| 时间戳异常 / 解析失败 / 跳过 | 0 / 0 / 0 |

## 本次结果解读

- 本次共评测 **20** 条 case，其中 **20** 条生成了完整的 Retrieval、Answer 和 Judge 产物，**0** 条链路不完整。
- Retrieval 实际计分 **20** 条，Hit@10 为 **100.0%**，Recall@10 为 **100.0%**，MRR 为 **0.9625**。
- Answer/Judge 实际计分 **20** 条，答案准确率为 **95.0%**。
- 当前数量最多的失败根因是 `RETRIEVAL_WRONG_CHUNK`（1 条）；应优先打开对应 case Trace，从上游向下排查。

## 总览

| 指标 | 结果 |
| --- | ---: |
| Case 总数 | 20 |
| 完整生成 Retrieval、Answer、Judge 产物 | 20 |
| 链路产物不完整 | 0 |
| Retrieval 实际计分数 | 20 |
| Hit@10 | 100.0% |
| Recall@10 | 100.0% |
| MRR | 0.9625 |
| Answer 准确率 | 95.0%（20 条已计分） |
| Pipeline Success Rate | 100.0% |
| 严格端到端成功率（Retrieval PASS 且 Answer PASS） | 95.0% |
| Add 失败 | 0 |
| Retrieval 失败 | 0 |
| Answer 失败 | 0 |
| Judge 可疑 | 0 |

## 延迟与 API 稳定性

| 阶段 | Avg ms | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: | ---: |
| Add | 32.4 | 32.8 | 37.6 | 39.0 |
| Index | 804.1 | 790.8 | 874.2 | 897.7 |
| Search | 19.0 | 19.9 | 32.1 | 36.8 |
| Answer | 1684.4 | 1599.7 | 2470.7 | 3014.7 |
| Judge | 3611.0 | 2112.0 | 8440.2 | 17890.9 |
| End-to-End | 6151.0 | 4385.8 | 10929.3 | 21589.8 |

- End-to-End 为每条 Case 的 Add + Index + Search + Answer + Judge 记录耗时之和，不包含服务启动、关闭和编排开销。
- Memory API：Index 请求 20，Search 请求 20，HTTP 2xx 40。
- LLM API：Answer 请求 20，Judge 请求 20，重试 0，超时 0，错误 0。

## Index / Memory Processing

| 指标 | 结果 |
| --- | --- |
| Indexed Documents / Chunks | 980 / 1537 |
| Average Chunks / Session | 1.5684 |
| Embedding | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0; chunks=0 |
| Extraction | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0 |

## LLM Token 与 Cost

| 阶段 | Input Tokens | Cache Hit | Cache Miss | Output Tokens | Cost USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Answer | 222193 | 9344 | 212849 | 1840 | 0.03034022 |
| Judge | 14384 | 10368 | 4016 | 7204 | 0.00260839 |
| Total | - | - | - | - | 0.03294861 |

- Cost 按 Runner 保存的价格表计算；旧产物没有价格表时按报告构建时匹配的内置价格表回算。缓存未分类的 Input Token 按 Cache Miss 计费。
- Answer Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Judge Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Pricing Source：Answer=https://api-docs.deepseek.com/quick_start/pricing；Judge=https://api-docs.deepseek.com/quick_start/pricing。

## 按 Question Type 拆分

| Question Type | Cases | Hit@10 | Recall@10 | MRR | Accuracy | Search Avg ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| single-session-user | 20 | 100.0% | 100.0% | 0.9625 | 95.0% | 19.0 |

## Retrieval 条件下的 Answer Accuracy

| 条件 | Cases | Correct | Accuracy |
| --- | ---: | ---: | ---: |
| full_evidence_recall | 20 | 19 | 95.0% |
| partial_evidence_recall | 0 | 0 | NOT_APPLICABLE |
| zero_evidence_recall | 0 | 0 | NOT_APPLICABLE |
| evidence_found | 20 | 19 | 95.0% |
| has_gold_evidence | 20 | 19 | 95.0% |
| no_gold_evidence | 0 | 0 | NOT_APPLICABLE |

## 重点场景结论

- 单 Evidence Accuracy：**95.0%**；多 Evidence Accuracy：**NOT_RECORDED**；差值（多 - 单）：**NOT_RECORDED**。
- Temporal Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- Knowledge Update Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- 至少找到部分 Evidence 后的 Answer Accuracy：**95.0%**。
- 样本量只有 20 条，各场景差值用于定位信号，不作为统计显著性结论。

## Retrieval × Answer 四象限

| 分类 | 数量 | 如何理解 |
| --- | ---: | --- |
| A：Retrieval ✓ + Answer ✓ | 19 | 正常成功，Memory 找对且最终答对 |
| B：Retrieval ✗ + Answer ✗ | 1 | 优先排查检索召回和排序 |
| C：Retrieval ✓ + Answer ✗ | 0 | 排查上下文丢失、Answer 推理或 Judge |
| D：Retrieval ✗ + Answer ✓ | 0 | 可能依靠模型先验猜对，不能证明 Memory 有效 |
| 未计分 | 0 | Answer/Judge 产物不完整 |

## 主要根因分布

| 根因标签 | 数量 | 含义 |
| --- | ---: | --- |
| `PASS` | 19 | 检索、上下文传递和最终回答均通过 |
| `DATA_ERROR` | 0 | 数据集字段或 Evidence 引用不完整 |
| `ADD_FAILURE` | 0 | Evidence 未正确进入 Memory 输入 |
| `INDEX_FAILURE` | 0 | Memory 索引阶段失败 |
| `RETRIEVAL_MISS` | 0 | TopK 和候选结果中均未找到 Evidence |
| `RETRIEVAL_PARTIAL` | 0 | 只找到了部分 Evidence |
| `RETRIEVAL_LOW_RANK` | 0 | 找到了 Evidence，但排名低于 TopK |
| `RETRIEVAL_WRONG_CHUNK` | 1 | 命中 session，但返回片段不含标注 Evidence |
| `CONTEXT_LOSS` | 0 | Evidence 内容在检索返回或 Answer 上下文中丢失 |
| `CONTEXT_TRUNCATION` | 0 | Answer 输入在客户端发生截断 |
| `ANSWER_FAILURE` | 0 | Evidence 已到达 Answer 阶段，但生成失败或答案错误 |
| `JUDGE_SUSPECT` | 0 | Judge 失败或判分结果存在疑点，需要人工复核 |
| `API_FAILURE` | 0 | Memory 或 LLM API 请求失败 |
| `TIMEOUT` | 0 | 某个 API 阶段超时 |
| `PIPELINE_FAILURE` | 0 | 链路产物缺失，无法完成该 case 的评测 |

## 进一步排查入口

- [按失败优先级排列的 Case 索引](trace_index.md)
- [Judge 人工复核队列](judge_review.md)
- 机器可读汇总：`trace_summary.json`

## 开发侧结论

- Memory 是否全部成功写入：**是**。
- Evidence 是否全部写入：**是**。
- Search 是否稳定完成：**是**。
- Retrieval Miss/Partial 0 条，Low-rank 0 条，Wrong-chunk 1 条。
- Context Loss/Truncation 共 0 条；Judge Suspect 共 0 条。
- 平均耗时最大的阶段：**Judge**；数量最大的失败根因：**RETRIEVAL_WRONG_CHUNK**。
- 多 Evidence 相比单 Evidence：**NOT_RECORDED**；Temporal 相比总体：**NOT_RECORDED**；Knowledge Update 相比总体：**NOT_RECORDED**。
- Evidence 找到后的 Answer Accuracy：**95.0%**。
- 是否存在 Judge 误判：**尚不能确认**；自动可疑检测为 0，但没有人工复核标签，不能据此证明 Judge 无误判。
- 代码可复现状态：**PASS_DIRTY_WITH_SOURCE_SNAPSHOT**。
- 本 run 已冻结 Dataset、Case Selection、TopK、模型、Prompt、Memory Config Hash 与 Memory Version；Eval Code 是否可严格复现以上一条状态为准。

## 下一版 Runner 需要补充的可观测字段

- OpenAI-compatible 接口没有暴露服务端 Prompt 截断状态；当前已记录客户端是否截断。
- 人工 Judge 复核仍需手工填写，框架不会自动伪造人工结论。
