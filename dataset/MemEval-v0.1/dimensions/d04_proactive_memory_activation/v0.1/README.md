# D04 v0.1

本目录按照开发文档第 12 节构建 D04 的 38 条主动记忆激活样本。

- `cases/` 与 `contexts/`：包含机器构建并通过结构校验的 19 组正负 Activation Pair。
- Positive 共 19 条：10 条来自 `implicit_choice`，9 条来自 `implicit_persona`；偏好位于历史对话，最终 Query 不直接附带偏好。
- Negative 共 19 条：来自相同行的 `explicit` 数据，偏好作为当前输入事件紧邻 Query，不应调用长期记忆。
- 每一对保持相同的 Preference、最终 Query、Topic 和 Answer Criteria，只改变偏好的可见位置。
- 19 组人工审核已全部通过，38 条 Gold 已标记为 `human_review_approved`，可以用于最终 Activation 指标。
- 所有 README 均使用中文；字段名、数据集名和指标名保留原始英文。

## 人工审核合并结果

- 审核人：lrz
- 修订历史证据：10 组、10 个事件。
- 修订 Answer Criteria：2 组。
- 所有修订均保留来源引用，并在事件元数据中记录原内容哈希与审核来源。

## 最终审核清理状态

人工审核已经完成，结论、审核人、时间、修复摘要及原工作目录聚合哈希已压缩到正式 Case 和 Manifest。
审核工作目录在全局298 Case Benchmark Audit 通过后移除，不再作为运行时依赖。
