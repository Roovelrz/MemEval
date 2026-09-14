# D01 v0.1

本目录按照开发文档第8、9节构建 D01 的37条记忆抽取与写入样本。

- `contexts/`：按有限评分窗口保存规范化事件。
- `cases/`：保存公共信封、最终 `write` Gold Payload 和人工审核 annotation。
- 37份人工审核均已完成并通过；最终 Gold 已正式并入维度目录。
- 每条 Case 保留审核人、审核时间、检查项和审核说明；Manifest 保存原提交聚合哈希。
- 当前状态为 `complete`，可以用于 Write Precision 与 Write Recall。

## 评测口径（当前 Runner）

- 指标基于 Gold `gold_memories.evidence_event_ids` 与系统实际持久化内容的
  对齐：`memory_recall` = 写入内容覆盖 Gold 记忆证据的比例；`memory_precision`
  = 写入事件中属于 Gold 记忆证据的比例（无写入时为 `None`，不伪造 0）。
- 逐字全量写入会因存入 `non_memory_event_ids` 噪声而失分；抽取式系统需
  同时保事实、去噪声。
- 无记忆对照（`--memory-adapter off`）下 recall 如实为 0。
