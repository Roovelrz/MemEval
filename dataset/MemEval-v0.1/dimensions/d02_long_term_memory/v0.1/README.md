# D02 v0.1

本目录按照开发文档第 10 节构建 D02 的 37 条纯检索样本。

- `contexts/`：将完整的 LongMemEval-S haystack 映射为规范化事件。
- `cases/`：保存公共信封和原生 `retrieval` Gold Payload。
- `gold_evidence_ids`：以会话为粒度保留 LongMemEval 的 `answer_session_ids`。
- `gold_answer`：原样保留源数据中的值及其数据类型，不进行重新标注。
- 本纯检索切片排除了 LongMemEval 的 `_abs` 拒答变体。
- 上下文有意移除了 `has_answer` 及所有 Gold 标签元数据，避免答案泄漏。

## 评测口径（当前 Runner）

- 指标为 Hit@K / Recall@K / MRR，按 `gold_evidence_ids`（session 粒度）计算。
- Dashboard 以 **K=3 为主指标**（Hit@3 / Recall@3 / MRR@3），K=1/3/5/10 的
  完整分布保存在 `metrics_by_k`，鼠标悬停展示。
- 无 Gold 证据的 case 标记 `retrieval_evaluated=False`，不进入均值。
