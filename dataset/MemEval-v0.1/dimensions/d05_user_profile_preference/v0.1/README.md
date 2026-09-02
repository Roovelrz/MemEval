# D05 v0.1

本目录按照开发文档第 13 节构建 PersonaMem-v2 用户画像与偏好评测集。

- 最终包含37个不同 Persona、37个32K Context、37个 Profile Case。
- 每个 Persona 保留3个经审核和修复的 Gold Profile Item，共111个；满足文档规定的3至8个范围。
- 人工审核发现原始 PersonaMem `preference` 标签普遍比可见对话证据更具体，37个初稿均被标记为 `needs_revision`。
- 修复时没有引入新数据：删除证据薄弱条目，对保留条目作保守证据化改写，必要时切换到同一 Persona 的其他源行作为最终 Query。
- 9条 Gold Answer 已移除虚构时间、未提供人物或超出证据的画像细节。
- 只使用 text 32K；排除泄漏完整 Persona 的 system prompt，不伪造源数据没有提供的事件时间。
- 当前状态为 `complete`，可进入后续阶段。

## 最终审核清理状态

人工审核已经完成，结论、审核人、时间、修复摘要及原工作目录聚合哈希已压缩到正式 Case 和 Manifest。
审核工作目录在全局298 Case Benchmark Audit 通过后移除，不再作为运行时依赖。
