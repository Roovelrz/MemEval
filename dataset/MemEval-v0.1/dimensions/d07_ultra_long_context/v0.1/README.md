# D07 v0.1

本目录按照开发文档第15节构建 BEAM 超大规模长上下文评测集。

- 最终包含37个 Case：8个 Scale Group × 4档 = 32个 paired Case，另有5个 10M Stress Case。
- 8个 paired group 均来自同一条官方 BEAM-10M conversation 的连续窗口；固定起点后只扩大结束边界。
- 每组 Question、Answer、Gold Evidence 完全不变，Evidence 位于100K版本内，支持严格的 paired Recall Degradation。
- 5个 Stress Case 的 Gold Evidence 均位于所用约10M Context的8M估算 token之后。
- 原人工审核为12份 approved、1份 needs_revision；证据不足的 scale_group_04 已替换并重新审核通过。
- Context 使用 JSONL 流式存储；token 数采用 `ceil(character_count/4)` 估算，正式运行应另报模型 tokenizer 实际输入 token。
- 当前状态为 `complete_after_review_repair`，自动完整性检查和13份最终语义审核全部通过。

目录说明：

- `contexts/*.jsonl`：36个去重后的超长 Context 文件。
- `contexts/index.json`：Context 边界、规模、来源和哈希。
- `cases/`：最终37个 D07 Case。
- `manifest.json`：来源、构造方法、修复轨迹与最终文件哈希。

## 最终审核清理状态

人工审核已经完成，结论、审核人、时间、修复摘要及原工作目录聚合哈希已压缩到正式 Case 和 Manifest。
审核工作目录在全局298 Case Benchmark Audit 通过后移除，不再作为运行时依赖。
