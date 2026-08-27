# Trace 汇总报告

> 评测目录：`E:\LRZ_Workplace\fork\memory_eval_pipeline\results\en_full\reme\reme-en-local-20\Detailed Trace Report`  
> 排查原则：始终沿真实链路从上游向下检查——Add → Retrieval → Context → Answer → Judge。

## Run 基础信息

| 字段 | 值 |
| --- | --- |
| Run ID | `reme-en-local-20` |
| Dataset | LongMemEval 英文全量基准 / `local-d6f21ea9` |
| Case / Session / Turn / Evidence Session | 100 / 4824 / 49823 / 170 |
| Memory | ReMe `0.4.1.8` |
| TopK | 10 |
| Answer / Judge Model | `deepseek-v4-flash` / `deepseek-v4-flash` |
| Prompt Version | `longmemeval-answer-v2-structured-time` / `longmemeval-judge-v1` |
| Eval Commit | `fb4123b6225ea289cf2014d52ad1b07da2bc09d2`（dirty=True） |
| Eval Code Snapshot | `3afbe9fc4f2df83cd2e5424b7e79f2963210403f89bdc47fc34d88552c030577` |
| Reproducibility | `PASS_DIRTY_WITH_SOURCE_SNAPSHOT` |
| Start / End | 2026-08-26T09:24:40.181531+00:00 / 2026-08-26T10:12:49.221765+00:00 |

## Dataset 完整性

- Run 选中数据验收状态：**PASS_WITH_WARNINGS**；源数据验收状态：**NOT_RECORDED**。

| 指标 | 数量 |
| --- | ---: |
| 实际加载 Case / Session / Turn / Evidence Session | 100 / 4824 / 49823 / 170 |
| 缺失 Question / Gold Answer / Evidence ID | 0 / 0 / 0 |
| 重复 Session ID / Case ID | 4 / 0 |
| 时间戳异常 / 解析失败 / 跳过 | 0 / 0 / 0 |

## 本次结果解读

- 本次共评测 **100** 条 case，其中 **100** 条生成了完整的 Retrieval、Answer 和 Judge 产物，**0** 条链路不完整。
- Retrieval 实际计分 **100** 条，Hit@10 为 **98.0%**，Recall@10 为 **95.3%**，MRR 为 **0.9040**。
- Answer/Judge 实际计分 **100** 条，答案准确率为 **82.0%**。
- 当前数量最多的失败根因是 `RETRIEVAL_WRONG_CHUNK`（19 条）；应优先打开对应 case Trace，从上游向下排查。
- 有 **17** 条属于 C 象限：虽然答案判对，但 Retrieval 未通过，可能是模型猜对或利用了非 Evidence 信息，不能视为 Memory 成功。

## 总览

| 指标 | 结果 |
| --- | ---: |
| Case 总数 | 100 |
| 完整生成 Retrieval、Answer、Judge 产物 | 100 |
| 链路产物不完整 | 0 |
| Retrieval 实际计分数 | 100 |
| Hit@10 | 98.0% |
| Recall@10 | 95.3% |
| MRR | 0.9040 |
| Answer 准确率 | 82.0%（100 条已计分） |
| Pipeline Success Rate | 100.0% |
| 严格端到端成功率（Retrieval PASS 且 Answer PASS） | 65.0% |
| Add 失败 | 0 |
| Retrieval 失败 | 9 |
| Answer 失败 | 2 |
| Judge 可疑 | 0 |

## 延迟与 API 稳定性

| 阶段 | Avg ms | P50 ms | P95 ms | P99 ms |
| --- | ---: | ---: | ---: | ---: |
| Add | 31.2 | 30.8 | 39.1 | 43.4 |
| Index | 859.8 | 851.5 | 1027.9 | 1042.4 |
| Search | 18.3 | 20.4 | 29.5 | 30.6 |
| Answer | 6278.0 | 1899.9 | 7950.5 | 102375.9 |
| Judge | 2594.7 | 2200.9 | 5884.6 | 8244.4 |
| End-to-End | 9782.1 | 5644.6 | 12430.7 | 105083.6 |

- End-to-End 为每条 Case 的 Add + Index + Search + Answer + Judge 记录耗时之和，不包含服务启动、关闭和编排开销。
- Memory API：Index 请求 100，Search 请求 100，HTTP 2xx 200。
- LLM API：Answer 请求 105，Judge 请求 100，重试 5，超时 0，错误 2。

## Index / Memory Processing

| 指标 | 结果 |
| --- | --- |
| Indexed Documents / Chunks | 4824 / 7615 |
| Average Chunks / Session | 1.5786 |
| Embedding | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0; chunks=0 |
| Extraction | enabled=NO; status=NOT_APPLICABLE; calls=0; failures=0 |

## LLM Token 与 Cost

| 阶段 | Input Tokens | Cache Hit | Cache Miss | Output Tokens | Cost USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Answer | 1414389 | 294016 | 1120373 | 37942 | 0.16829922 |
| Judge | 72421 | 52608 | 19813 | 22155 | 0.00912452 |
| Total | - | - | - | - | 0.17742375 |

- Cost 按 Runner 保存的价格表计算；旧产物没有价格表时按报告构建时匹配的内置价格表回算。缓存未分类的 Input Token 按 Cache Miss 计费。
- Answer Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Judge Pricing（USD / 1M tokens）：hit=0.0028，miss=0.1400，output=0.2800，multiplier=1.0000。
- Pricing Source：Answer=https://api-docs.deepseek.com/quick_start/pricing；Judge=https://api-docs.deepseek.com/quick_start/pricing。

## 按 Question Type 拆分

| Question Type | Cases | Hit@10 | Recall@10 | MRR | Accuracy | Search Avg ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| multi-session | 30 | 96.7% | 87.8% | 0.8500 | 56.7% | 17.7 |
| single-session-user | 70 | 98.6% | 98.6% | 0.9271 | 92.9% | 18.6 |

## Retrieval 条件下的 Answer Accuracy

| 条件 | Cases | Correct | Accuracy |
| --- | ---: | ---: | ---: |
| full_evidence_recall | 91 | 81 | 89.0% |
| partial_evidence_recall | 7 | 0 | 0.0% |
| zero_evidence_recall | 2 | 1 | 50.0% |
| evidence_found | 98 | 81 | 82.7% |
| has_gold_evidence | 100 | 82 | 82.0% |
| no_gold_evidence | 0 | 0 | NOT_APPLICABLE |

## 重点场景结论

- 单 Evidence Accuracy：**92.9%**；多 Evidence Accuracy：**56.7%**；差值（多 - 单）：**-36.2 pp**。
- Temporal Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- Knowledge Update Accuracy：**NOT_RECORDED**，相对总体差值：**NOT_RECORDED**。
- 至少找到部分 Evidence 后的 Answer Accuracy：**82.7%**。
- 样本量只有 20 条，各场景差值用于定位信号，不作为统计显著性结论。

## Retrieval × Answer 四象限

| 分类 | 数量 | 如何理解 |
| --- | ---: | --- |
| A：Retrieval ✓ + Answer ✓ | 65 | 正常成功，Memory 找对且最终答对 |
| B：Retrieval ✓ + Answer ✗ | 2 | 排查上下文丢失、Answer 推理或 Judge |
| C：Retrieval ✗ + Answer ✓ | 17 | 可能依靠模型先验猜对，不能证明 Memory 有效 |
| D：Retrieval ✗ + Answer ✗ | 16 | 优先排查检索召回和排序 |
| 未计分 | 0 | Answer/Judge 产物不完整 |

## 主要根因分布

| 根因标签 | 数量 | 含义 |
| --- | ---: | --- |
| `PASS` | 65 | 检索、上下文传递和最终回答均通过 |
| `DATA_ERROR` | 0 | 数据集字段或 Evidence 引用不完整 |
| `ADD_FAILURE` | 0 | Evidence 未正确进入 Memory 输入 |
| `INDEX_FAILURE` | 0 | Memory 索引阶段失败 |
| `RETRIEVAL_MISS` | 2 | TopK 和候选结果中均未找到 Evidence |
| `RETRIEVAL_PARTIAL` | 7 | 只找到了部分 Evidence |
| `RETRIEVAL_LOW_RANK` | 0 | 找到了 Evidence，但排名低于 TopK |
| `RETRIEVAL_WRONG_CHUNK` | 19 | 命中 session，但返回片段不含标注 Evidence |
| `CONTEXT_LOSS` | 0 | Evidence 内容在检索返回或 Answer 上下文中丢失 |
| `CONTEXT_TRUNCATION` | 0 | Answer 输入在客户端发生截断 |
| `ANSWER_FAILURE` | 2 | Evidence 已到达 Answer 阶段，但生成失败或答案错误 |
| `JUDGE_SUSPECT` | 0 | Judge 失败或判分结果存在疑点，需要人工复核 |
| `API_FAILURE` | 0 | Memory 或 LLM API 请求失败 |
| `TIMEOUT` | 0 | 某个 API 阶段超时 |
| `PIPELINE_FAILURE` | 5 | 链路产物缺失，无法完成该 case 的评测 |

## 进一步排查入口

- [按失败优先级排列的 Case 索引](trace_index.md)
- [Judge 人工复核队列](judge_review.md)
- 机器可读汇总：`trace_summary.json`

## 开发侧结论

- Memory 是否全部成功写入：**是**。
- Evidence 是否全部写入：**是**。
- Search 是否稳定完成：**是**。
- Retrieval Miss/Partial 9 条，Low-rank 0 条，Wrong-chunk 19 条。
- Context Loss/Truncation 共 0 条；Judge Suspect 共 0 条。
- 平均耗时最大的阶段：**Answer**；数量最大的失败根因：**RETRIEVAL_WRONG_CHUNK**。
- 多 Evidence 相比单 Evidence：**-36.2 pp**；Temporal 相比总体：**NOT_RECORDED**；Knowledge Update 相比总体：**NOT_RECORDED**。
- Evidence 找到后的 Answer Accuracy：**82.7%**。
- 是否存在 Judge 误判：**尚不能确认**；自动可疑检测为 0，但没有人工复核标签，不能据此证明 Judge 无误判。
- 代码可复现状态：**PASS_DIRTY_WITH_SOURCE_SNAPSHOT**。
- 本 run 已冻结 Dataset、Case Selection、TopK、模型、Prompt、Memory Config Hash 与 Memory Version；Eval Code 是否可严格复现以上一条状态为准。

## 下一版 Runner 需要补充的可观测字段

- OpenAI-compatible 接口没有暴露服务端 Prompt 截断状态；当前已记录客户端是否截断。
- 人工 Judge 复核仍需手工填写，框架不会自动伪造人工结论。
