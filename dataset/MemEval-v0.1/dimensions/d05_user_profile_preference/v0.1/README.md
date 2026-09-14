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

## 评测口径（当前 Runner）

- PersonaMem 源数据是**单 session** 设计：session 级 recall 恒为 1，不能
  反映真实检索水平。主指标因此是 **needle 召回**——`profile_items.
  evidence_event_ids` 指向的证据事件文本是否出现在返回 chunk 中
  （`recall_at_k` / `hit_at_k` / `mrr` 均按 needle 口径覆盖）。
- session 级对齐的召回保留为 `session_recall_at_k` 参照值。
- 回答侧主指标为 `personalized_answer_accuracy`（Judge 判定是否依据用户
  偏好作答）。
