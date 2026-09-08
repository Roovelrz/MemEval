# MemEval Runner

阶段27的 `MemEvalRunner` 读取冻结 Case 的 `context_ref`，创建隔离命名空间，调用
System Adapter 写入，并按维度执行操作：

| 维度 | Runner 动作 | 当前 ReMe 结果范围 |
| --- | --- | --- |
| D01 | `list_memories` | 记录 Event 持久化覆盖率；语义记忆精确率/召回率为 `None` |
| D02 | `search` | Session 级 Hit、Recall、MRR |
| D03 | `search` + `query` | 检索可评分；Answer 未支持，所以状态为 `partial` |
| D04 | `get_trace` | ReMe 无主动激活决策 Trace，状态为 `unsupported` |
| D05 | `get_profile` + `search` | 检索指标可评分；ReMe 无画像提取，所以状态为 `partial` |
| D06 | `search` + `query` | 检索可评分；Answer 未支持，所以状态为 `partial` |
| D07 | `search` + `query` | 检索可评分；Answer 未支持，所以状态为 `partial` |
| D08 | identity 分流、生命周期删除、`search` | 分别记录允许召回与禁止/删除/Canary 暴露 |

每条 `results.jsonl` 都包含开发文档约定的 Run、Case、Dimension、System、Prediction、
Retrieved Memories、Trace、Latency、Cost、Metrics、Status 和 Error。单个 Case 失败会
留下 `error` 结果，后续 Case 继续执行。`run_summary.json` 按维度汇总已有数值指标和
不支持项；`None` 与 `unsupported` 不进入均值。

正式评分默认逐 Case 隔离：

```powershell
py -3.12 scripts/run_memeval.py --dataset MemEval-v0.1 --dimension D08 --limit 1 --run-id d08-smoke
```

运行期间 Retrieval、Answer、Judge 都会逐 Case 输出进度条、完成数、百分比、耗时和
预计剩余时间。默认启用断点续跑；进程中断后，使用完全相同的 `--run-id` 和 Retrieval
参数重新执行即可。Retrieval 跳过已有成功 Case，并重试错误 Case；Answer/Judge 按已有
输出 ID 跳过成功请求：

```powershell
py -3.12 scripts/run_memeval.py --dataset MemEval-v0.1 --run-id reme-full-20260908-132206 --answer-workers 2 --judge-workers 2
```

首次运行会写入 `retrieval_run_config.json`。续跑时若数据选择、TopK、Context Batch 或
ReMe 配置与首次运行不同，脚本会拒绝混合结果并要求使用新的 `--run-id`。`--no-resume`
可用于明确禁止复用已有 Run；如果目标目录已有结果，它会直接报错而不会覆盖。

阶段28提供性能专用 Context Batch Mode：

```powershell
py -3.12 scripts/run_memeval.py --dataset MemEval-v0.1 --dimension D03 --context-batch --run-id d03-batch
```

`--context-batch` 按 `context_id + tenant_id + user_id` 分组，并在复用前核对 Context
SHA-256。同一 `context_id` 内容不同会直接失败。批量模式执行 `ingest once / query N
times`，结果中的 `run_mode`、`reuse_context`、`context_cache.hit` 和
`ingest_owner_case_id` 会记录复用关系。D08 含状态变更和隐私动作，始终保持逐 Case
隔离，即使开启批量模式也不会复用其运行时。

两个模式的 `run_summary.json` 分别记录 `case_count`、`context_count` 和
`ingest_count`，不能把两种模式的吞吐或延迟混合比较。批量模式后续 Query 的
`latency.ingest` 为 `None`，不会伪造为零耗时；其 System Trace 和 Cost 范围标记为
Context Batch 累计值。

可重复使用 `--dimension` 和 `--case-id` 精确选择 Case，`--limit` 在筛选后生效。
默认使用本地 ReMe BM25 配置，不调用 LLM API。使用自定义混合检索时同时传入
`--reme-config` 与相应的 `--vector-weight`。运行产物默认位于
`results/memeval_v0_1/reme/<run-id>/`。
