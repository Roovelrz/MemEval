# LongMemEval-ZH-v0.1 翻译说明

## 你现在只做什么

只把每个文档中 `ZH_QUESTION`、`ZH_ANSWER` 或 `ZH_TURN` 边界里的占位行替换成简体中文。不要做截断、session 重排、摘要、事实校正、答案重写或新标注。

每次只翻译一个 session 文档。不要把整个 case 的几十个 session 一次交给翻译模型，以免漏译、合并 turn 或让模型根据上下文强化证据。

## 不同内容分别怎么翻译

### Question

- 保持原问题的询问对象、时间范围、人称、单复数、否定和不确定性。
- 译成自然中文，但不能加入原文没有的关键词或答案提示。
- `What did I ...?` 应继续保持用户第一人称，不能改成关于“该用户”的第三人称题目。
- 时间推理问题中的 before、after、first、last、most recent、how long 等关系必须精确保留。

### Gold answer

- 只翻译给定 answer，绝对不能根据历史对话重新生成答案。
- 保持答案粒度：原文是短语就译成短语，原文是完整解释才译成完整解释。
- 人名、品牌、型号、课程名、专业名可保留常用英文；有稳定中文译名时可写常用中文，必要时首次使用“中文（English）”。
- 数字、单位、日期、版本号、否定词和模糊词必须保留。不能把“可能”“大约”“通常”翻成确定事实。

### User turn

- 译成自然的中文对话，保持用户原有意图、语气和信息显式程度。
- 不要把隐含偏好提炼成“我的偏好是……”，也不要将零散事实总结成 profile。
- 保留代词指代和可能存在的歧义。不要为了顺畅而补出原文未说明的主语、地点或因果关系。
- 产品名、专有名词、数字、日期、金额、网址、文件名和代码原样或按统一术语表处理。

### Assistant turn

- 全文翻译，不能摘要，也不能删除重复、冗长或看起来不重要的部分。
- 保留 Markdown 层级、列表顺序、表格、代码块、引用和链接目标。
- 不要纠正原回答中的事实错误、逻辑错误或前后矛盾；这些也是原 benchmark 难度的一部分。
- 不要因为已经看到后续 question 或 gold answer，就改写 assistant 的措辞来突出证据。

### has_answer 与 evidence session

- `has_answer` 和 `is_evidence_session` 仅用于提醒，它们不是需要翻译的文本。
- `has_answer=true` 的 turn 与普通 turn 使用完全相同的翻译标准，不能加粗答案、增加同义解释或把隐含事实改成直接结论。
- 原 turn 没有 `has_answer` 时会显示 `NOT_PRESENT`；不要补写 true/false。

## 始终保持不变

- 所有 frontmatter 内容，包括 `question_id`、`question_type`、`question_date`、`session_id`、`timestamp`、`answer_session_ids`。
- `English source — DO NOT EDIT` 区域。
- 所有 `SOURCE_*` 与 `ZH_*` HTML 边界标记。
- turn 数量、顺序和 role。
- 原文中的代码、URL、文件路径、ID、电子邮箱及结构化字面量；周几可以翻译，但日期和时间值不能改变。

## 交给翻译模型时怎么说

一次只附带一个 Markdown 文档，不要同时附带同一 case 的其他 session。

翻译 `question_answer.md` 时使用：

> 请编辑附带的 LongMemEval 翻译表。只把 `ZH_QUESTION` 和 `ZH_ANSWER` 边界内的占位行替换为简体中文，可以使用多行；其他字符必须保持原样。Question 保持原问题的人称、时间关系、歧义和信息量。Gold answer 只能翻译给定答案，禁止根据问题或常识重新生成答案。不要添加解释，返回完整 Markdown。

翻译单个 `session_*.md` 时使用：

> 请编辑附带的 LongMemEval session 翻译表。逐 turn 把每个 `ZH_TURN_*` 边界内的占位行替换为完整的简体中文翻译，可以使用多行；其他字符必须保持原样。保留原信息显式程度、歧义、重复、列表、Markdown、数字、日期、专有名词和错误，不摘要、不纠错、不补充事实。即使看到 `has_answer=true` 或 `is_evidence_session=true`，也禁止突出、强化或解释证据。不要添加说明，返回完整 Markdown。

如果翻译模型无法保证只改中文块，让它只按 turn 序号输出译文，再由你粘贴进对应 `ZH_*` 区域；不要接受它重排或重写整个文档。

## 一致性规则

- 使用简体中文和中文标点；代码、路径、URL 内部标点不改。
- 同一 case 内的人名、地名、品牌、课程、专业和技术术语保持同译。
- 遇到没有把握的专有名词，优先保留英文，并在 `GLOSSARY.md` 记录决定。
- 不要把金额、英制/公制单位自行换算，因为换算会改变可检索的原始表述。

## 每个文档完成后的检查

1. 所有对应 `ZH_*` 区域都已替换占位行，且不为空。
2. 没有编辑 source、元数据或边界标记。
3. 没有漏掉列表项、段落、重复内容和最后一句。
4. 数字、日期、专有名词、否定与时间关系逐项对照无变化。
5. 没有总结、强化 evidence 或重新生成 answer。
6. 保存为 UTF-8 Markdown。

完成翻译后先不要手工合并文件。通知 Codex 进行结构校验、占位符扫描、抽样语义检查和中文数据重组。
