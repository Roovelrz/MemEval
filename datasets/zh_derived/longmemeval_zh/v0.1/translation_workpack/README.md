# LongMemEval-ZH-v0.1 Translation Workpack

本翻译包包含 100 个分层样本、4801 个 session、49691 个 turn。

## 开始顺序

1. 完整阅读 `TRANSLATION_GUIDE.md`。
2. 在 `GLOSSARY.md` 记录统一的专有名词译法。
3. 打开 `translation_index.csv`，从第一条 case 开始。
4. 先翻译该 case 的 `question_answer.md`。
5. 再按文件名前的三位序号逐个翻译 `sessions/`，每次只处理一个 session。
6. 可以在 CSV 的 `translator_status` 列把 `TODO` 改为 `DONE`；不要修改其余列。
7. 全部完成后停止，不要自行拆分、截断或生成最终数据集。

## 目录含义

- `cases/<question_id>/question_answer.md`：只翻译 question 和官方 gold answer。
- `cases/<question_id>/sessions/*.md`：逐 turn 翻译完整历史。
- `sampling_manifest.json`：抽样方法、题型配额和原数据哈希，只读。
- `structure_lock.json`：原始结构和文本哈希，只读，供后续自动校验。
- `translation_index.csv`：翻译进度索引。
- `GLOSSARY.md`：译名与风格决定记录。

原始数据没有被复制或改写；本目录只是一组人工可编辑翻译表。中文完整集及 32K/64K 派生集将在翻译通过校验后另行构建。
