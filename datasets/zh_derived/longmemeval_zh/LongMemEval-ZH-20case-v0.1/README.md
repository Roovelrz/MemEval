# LongMemEval-ZH-20-v0.1

这是给 Memory Eval 使用的冻结 Clean 数据集。`dataset.json` 是唯一的评测输入；

## 数据范围

- 20 个 case
- 964 个 session
- 10,055 个 turn
- 34 个 evidence session
- 10,095 个翻译 block：20 个问题 + 20 个 gold answer + 10,055 个 turn

Clean 数据只保留中文评测内容、角色、时间、session/evidence 元数据和 `has_answer`。英文原文、SOURCE/ZH 标记、翻译提示、TODO/status 没有进入 `dataset.json`。

## 验收与冻结文件

- `manifest.json`：版本、来源、构建信息、hash 和冻结规则
- `integrity_report.json`：与原始 LongMemEval 的结构一致性验收
- `semantic_review_manifest.json`：所有 evidence session 和固定随机种子抽取的 30 个 distractor session 的中英对照审阅材料；不是 Eval 输入
- `manual_review_completion.json`：人工审阅范围和结论

原始翻译 Markdown 工作文件仍保留在同级的 `v0.1/translation_workpack`，没有被 Clean exporter 覆盖。
