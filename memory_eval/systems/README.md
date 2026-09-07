# System Adapter

本目录是正式 MemEval Case 与被测记忆系统之间的薄层接口。

`ReMeSystemAdapter` 把八个维度的 `Context Event` 按 Session
转换为现有 ReMe Adapter 已支持的输入，并直接复用现有的启动、写入、索引、检索
和清理逻辑，没有重写 ReMe。

阶段25定义统一接口、`SystemCapabilities` 和 `SystemOperationResult`。
可选操作返回 `status="ok"` 或 `status="unsupported"`；后者包含原因且没有分数，
阶段27 Evaluator/Runner 必须保留这个状态，不能将其转换为零分。

阶段26在 Wrapper 中增加命名空间、删除与观察接口。能力声明以当前文件/BM25
后端为准：

| 能力 | 支持 | 观察范围 |
| --- | --- | --- |
| `write_trace` | 是 | Adapter 的写入/重建索引结果，记忆单位是 Session 文件 |
| `retrieval` | 是 | 复用原有检索与 Session 去重 |
| `delete` | 是 | 删除 Session、Event 或源 memory ID 对应的内容，再重建索引 |
| `user_isolation` | 是 | 每个显式 namespace 使用独立目录、索引和服务端口 |
| `latency_stats` | 是 | 文件写入耗时，以及各类操作的次数和累计耗时 |
| `activation_trace` | 否 | 操作记录不等于主动激活的决策轨迹 |
| `profile` | 否 | 当前后端没有画像提取 |
| `cost_stats` | 否 | 费用为 `None`，没有伪造零费用 |

`query()` 当前返回 `unsupported`：该后端提供检索，原有 Answer/LLM 流程仍在
现有框架中独立执行。`get_profile()` 同样返回 `unsupported`。

调用顺序：

```python
runtime = adapter.create_namespace(
    namespace="user-a", workspace=work_root, case=case,
    context_path=context_path, dataset_id="MemEval-v0.1",
    port=25001, service_log_path=log_path,
)
try:
    adapter.ingest(runtime)
    memories = adapter.list_memories(runtime)
    result = adapter.search(runtime, query="question", top_k=3)
    adapter.delete(runtime, memory_ids=["source-memory-id"])
    trace = adapter.get_trace(runtime)
    stats = adapter.get_stats(runtime)
finally:
    adapter.cleanup(runtime)
```

调用方必须把属于该命名空间的 Context 传入，并为并行命名空间分配不同端口。
Wrapper 不从 Gold 的 allowed/forbidden 列表推断授权，也不代替 Runner 把混合用户
Context 分流。重复使用活动目录或端口会报错。原有 `open_case/close_case` 仍可使用。

`open_case/create_namespace` 延续阶段24的行为，先写入初始文件，`ingest` 再建立索引。
`list_memories` 读取实际 Session 文件，返回 `indexed` 状态、Event 和源 memory ID；
这些是该基线的持久化记忆，不是模型生成的摘要或画像。一个 memory ID 横跨多个
Session 时会全部删除；共享 Session 中其他记忆仍然保留。未知 ID 报错且不改内容。
重建索引失败时不返回成功，且禁止搜索可能残留的旧索引。

`reset` 恢复 Case 初始文件并清空操作记录，随后须重新 `ingest`；因此会恢复本轮
删除的初始测试数据。`cleanup` 关闭服务并清理工作目录，允许重复调用。
Context 中的 `metadata.operation="delete"` 是生命周期动作，不作为记忆写入；
阶段27 Runner 负责按事件顺序执行它，而不是在加载 Context 时自动执行。

`get_trace` 返回 Adapter 操作结果；`get_stats` 按操作分类聚合。删除耗时包含重建
索引，所以不能把各类耗时相加作为总运行时间。当前不提供完整系统内部 Trace。

安装 ReMe 后运行 `python -B scripts/smoke_reme_system.py`，可用真实 BM25 服务
检查正向检索、双命名空间隔离、局部删除、重置及全部删除。脚本只使用本地服务，
无需 LLM API，成功后清理临时目录。

阶段27 Runner 完成前，`MemEval-v0.1` 仍保持 `reserved`。

以后接入其他 Memory System 时，在本目录增加新的实现即可；不需要修改
Dataset Builder，也不需要让 Runner 理解具体系统的私有格式。
