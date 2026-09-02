# D06 v0.1

本目录按照开发文档第 14 节构建 MemoryAgentBench 动态更新与冲突评测集。

- 只使用官方 `Conflict_Resolution`，保留8个官方 Context，并以 `role=document` 表示长文档。
- 最终包含37个 Question-level Case：19个 multi-hop、18个 single-hop。
- 原始人工审核完成37份：33份直接通过，4份确认存在不可安全原地修订的源语义问题。
- 4条异常 Case 已在相同 source、相同 MH 类型和相同配额内替换；替代项均完成关系链语义校对。
- 原始缺失的时间和 `question_types` 没有被伪造；SH/MH 只依据官方 source 名称派生。
- 当前状态为 `complete_after_replacement`，自动完整性检查和37份最终语义审核均已通过。

关键文件：

- `cases/`：最终37条 Case。
- `contexts/`：8个官方 Context。
- `manifest.json`：最终计数、修订轨迹和文件哈希。

## 最终审核清理状态

人工审核已经完成，结论、审核人、时间、修复摘要及原工作目录聚合哈希已压缩到正式 Case 和 Manifest。
审核工作目录在全局298 Case Benchmark Audit 通过后移除，不再作为运行时依赖。
