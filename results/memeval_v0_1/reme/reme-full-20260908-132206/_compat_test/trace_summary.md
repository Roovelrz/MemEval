# Trace 汇总报告

> 评测目录：`E:\LRZ_Workplace\fork\memory_eval_pipeline\results\memeval_v0_1\reme\reme-full-20260908-132206`  
> 排查原则：始终沿真实链路从上游向下检查——Add → Retrieval → Context → Answer → Judge。

## Run 基础信息

| 字段 | 值 |
| --- | --- |
| Run ID | `reme-full-20260908-132206` |
| Dataset | Agent Memory Eval / `v0.1` |
| Case / Session / Turn / Evidence Session | 298 / NOT_RECORDED / NOT_RECORDED / NOT_RECORDED |
| Memory | ReMe `0.4.1.8` |
| TopK | 10 |
| Answer / Judge Model | `deepseek-v4-flash` / `deepseek-v4-flash` |
| Prompt Version | `longmemeval-answer-v2-structured-time` / `longmemeval-judge-v1` |
| Eval Commit | `NOT_RECORDED`（dirty=NOT_RECORDED） |
| Eval Code Snapshot | `NOT_RECORDED` |
| Reproducibility | `PARTIAL_DIRTY_WITHOUT_SOURCE_SNAPSHOT` |
| Start / End | 2026-09-08T07:16:33.196985+00:00 / 2026-09-08T07:25:57.270484+00:00 |

## Dataset 完整性

- Run 选中数据验收状态：**NOT_RECORDED**；源数据验收状态：**NOT_RECORDED**。

| 指标 | 数量 |
| --- | ---: |
| 实际加载 Case / Session / Turn / Evidence Session | NOT_RECORDED / NOT_RECORDED / NOT_RECORDED / NOT_RECORDED |
| 缺失 Question / Gold Answer / Evidence ID | NOT_RECORDED / NOT_RECORDED / NOT_RECORDED |
| 重复 Session ID / Case ID | NOT_RECORDED / NOT_RECORDED |
| 时间戳异常 / 解析失败 / 跳过 | NOT_RECORDED / NOT_RECORDED / NOT_RECORDED |

## 本次结果解读

- 本次共评测 **298** 条 case，其中 **298** 条完成了各自适用的评测阶段，**0** 条链路不完整。
- Retrieval 实际计分 **223** 条，Hit@10 为 **98.9%**，Recall@10 为 **97.0%**，MRR 为 **0.9248**。
- Answer/Judge 实际计分 **186** 条，答案准确率为 **33.9%**。
- 当前数量最多的失败根因是 `ADD_FAILURE`（182 条）；应优先打开对应 case Trace，从上游向下排查。
- 有 **63** 条属于 C 象限：虽然答案判对，但 Retrieval 未通过，可能是模型猜对或利用了非 Evidence 信息，不能视为 Memory 成功。

## 总览

| 指标 | 结果 |
| --- | ---: |
| Case 总数 | 298 |
| 完整生成 Retrieval、Answer、Judge 产物 | 298 |
| 链路产物不完整 | 0 |
| Retrieval 实际计分数 | 223 |
| Hit@10 | 98.9% |
| Recall@10 | 97.0% |
| MRR | 0.9248 |
| Answer 准确率 | 33.9%（186 条已计分） |
| Pipeline Success Rate | 100.0% |
| 严格端到端成功率（Retrieval PASS 且 Answer PASS） | 0.0% |
| Add 失败 | 182 |
| Retrieval 失败 | 0 |
| Answer 失败 | 0 |
| Judge 可疑 | 0 |

## 延迟与 API 稳定性

| 阶段 | Avg ms | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: | ---: |
| Add | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED |
| Index | 733.4 | 259.5 | 1578.5 | 9218.2 |
| Search | 18.0 | 18.3 | 27.1 | 29.4 |
| Answer | 14468.2 | 2588.4 | 80366.4 | 156225.5 |
| Judge | 3423.9 | 1882.4 | 7754.5 | 23568.4 |
| End-to-End | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED |

- End-to-End 为每条 Case 的 Add + Index + Search + Answer + Judge 记录耗时之和，不包含服务启动、关闭和编排开销。
- Memory API：Index 请求 NOT_RECORDED，Search 请求 NOT_RECORDED，HTTP 2xx NOT_RECORDED。
- LLM API：Answer 请求 198，Judge 请求 186，重试 12，超时 0，错误 3。

## Index / Memory Processing

| 指标 | 结果 |
| --- | --- |
| Indexed Documents / Chunks | 3221 / 67394 |
| Average Chunks / Session | 290.4914 |
| Embedding | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0; chunks=NOT_RECORDED |
| Extraction | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0 |

## LLM Token 与 Cost

| 阶段 | Input Tokens | Cache Hit | Cache Miss | Output Tokens | Cost USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Answer | 1111576 | 167680 | 943896 | 221670 | 0.19468254 |
| Judge | 138527 | 98560 | 39967 | 67860 | 0.02487215 |
| Total | - | - | - | - | 0.21955469 |

- Cost 按 Runner 保存的价格表计算；旧产物没有价格表时按报告构建时匹配的内置价格表回算。缓存未分类的 Input Token 按 Cache Miss 计费。
- Answer Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Judge Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Pricing Source：Answer=https://api-docs.deepseek.com/quick_start/pricing；Judge=https://api-docs.deepseek.com/quick_start/pricing。

## 按 Question Type 拆分

| Question Type | Cases | Hit@10 | Recall@10 | MRR | Accuracy | Search Avg ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D01 | 37 | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED |
| D02 | 37 | 100.0% | 96.6% | 1.0000 | 83.8% | 18.9 |
| D03 | 38 | 94.7% | 88.8% | 0.6953 | 21.1% | 17.3 |
| D04 | 38 | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED |
| D05 | 37 | 100.0% | 100.0% | 1.0000 | 10.8% | 19.5 |
| D06 | 37 | 100.0% | 100.0% | 1.0000 | 32.4% | 18.8 |
| D07 | 37 | 100.0% | 100.0% | 0.9347 | 21.6% | 18.1 |
| D08 | 37 | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | NOT_RECORDED | 15.4 |

## Retrieval 条件下的 Answer Accuracy

| 条件 | Cases | Correct | Accuracy |
| --- | ---: | ---: | ---: |
| full_evidence_recall | 176 | 61 | 34.7% |
| partial_evidence_recall | 8 | 2 | 25.0% |
| zero_evidence_recall | 2 | 0 | 0.0% |
| evidence_found | 184 | 63 | 34.2% |
| has_gold_evidence | 279 | 63 | 33.9% |
| no_gold_evidence | 19 | 0 | NOT_RECORDED |

## 重点场景结论

- 单 Evidence Accuracy：**30.8%**；多 Evidence Accuracy：**51.9%**；差值（多 - 单）：**+21.0 pp**。
- Temporal Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- Knowledge Update Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- 至少找到部分 Evidence 后的 Answer Accuracy：**34.2%**。
- 样本量只有 20 条，各场景差值用于定位信号，不作为统计显著性结论。

## Retrieval × Answer 四象限

| 分类 | 数量 | 如何理解 |
| --- | ---: | --- |
| A：Retrieval ✓ + Answer ✓ | 0 | 正常成功，Memory 找对且最终答对 |
| B：Retrieval ✓ + Answer ✗ | 0 | 排查上下文丢失、Answer 推理或 Judge |
| C：Retrieval ✗ + Answer ✓ | 63 | 可能依靠模型先验猜对，不能证明 Memory 有效 |
| D：Retrieval ✗ + Answer ✗ | 123 | 优先排查检索召回和排序 |
| 未计分 | 112 | Answer/Judge 不适用或产物不完整 |

## 主要根因分布

| 根因标签 | 数量 | 含义 |
| --- | ---: | --- |
| `PASS` | 37 | 检索、上下文传递和最终回答均通过 |
| `DATA_ERROR` | 0 | 数据集字段或 Evidence 引用不完整 |
| `ADD_FAILURE` | 182 | Evidence 未正确进入 Memory 输入 |
| `INDEX_FAILURE` | 0 | Memory 索引阶段失败 |
| `RETRIEVAL_MISS` | 0 | TopK 和候选结果中均未找到 Evidence |
| `RETRIEVAL_PARTIAL` | 0 | 只找到了部分 Evidence |
| `RETRIEVAL_LOW_RANK` | 0 | 找到了 Evidence，但排名低于 TopK |
| `RETRIEVAL_WRONG_CHUNK` | 0 | 命中 session，但返回片段不含标注 Evidence |
| `CONTEXT_LOSS` | 0 | Evidence 内容在检索返回或 Answer 上下文中丢失 |
| `CONTEXT_TRUNCATION` | 0 | Answer 输入在客户端发生截断 |
| `ANSWER_FAILURE` | 0 | Evidence 已到达 Answer 阶段，但生成失败或答案错误 |
| `JUDGE_SUSPECT` | 0 | Judge 失败或判分结果存在疑点，需要人工复核 |
| `API_FAILURE` | 0 | Memory 或 LLM API 请求失败 |
| `TIMEOUT` | 0 | 某个 API 阶段超时 |
| `PIPELINE_FAILURE` | 0 | 链路产物缺失，无法完成该 case 的评测 |
| `PRIVACY_FAILURE` | 0 | 敏感信息、跨用户记忆或已删除记忆被不当召回 |
| `UNSUPPORTED_CAPABILITY` | 38 | 系统未暴露该维度要求的能力，不折算成零分 |
| `PARTIAL_CAPABILITY` | 41 | 该维度只完成了系统当前支持的部分指标 |

## 进一步排查入口

- [按失败优先级排列的 Case 索引](trace_index.md)
- [Judge 人工复核队列](judge_review.md)
- 机器可读汇总：`trace_summary.json`

## 开发侧结论

- Memory 是否全部成功写入：**否**。
- Evidence 是否全部写入：**否**。
- Search 是否稳定完成：**否**。
- Retrieval Miss/Partial 0 条，Low-rank 0 条，Wrong-chunk 0 条。
- Context Loss/Truncation 共 0 条；Judge Suspect 共 0 条。
- 平均耗时最大的阶段：**Answer**；数量最大的失败根因：**ADD_FAILURE**。
- 多 Evidence 相比单 Evidence：**+21.0 pp**；Temporal 相比总体：**NOT_RECORDED**；Knowledge Update 相比总体：**NOT_RECORDED**。
- Evidence 找到后的 Answer Accuracy：**34.2%**。
- 是否存在 Judge 误判：**尚不能确认**；自动可疑检测为 0，但没有人工复核标签，不能据此证明 Judge 无误判。
- 代码可复现状态：**PARTIAL_DIRTY_WITHOUT_SOURCE_SNAPSHOT**。
- 本 run 已冻结 Dataset、Case Selection、TopK、模型、Prompt、Memory Config Hash 与 Memory Version；Eval Code 是否可严格复现以上一条状态为准。

## 下一版 Runner 需要补充的可观测字段

- OpenAI-compatible 接口没有暴露服务端 Prompt 截断状态；当前已记录客户端是否截断。
- 人工 Judge 复核仍需手工填写，框架不会自动伪造人工结论。
- 本次运行使用了 dirty 工作区且没有源码快照；仅凭 Git commit 无法严格还原当时运行代码。
