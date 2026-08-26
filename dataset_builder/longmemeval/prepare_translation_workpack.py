"""Create the human-editable LongMemEval-ZH-v0.1 translation workpack."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


SAMPLE_QUOTAS = {
    "single-session-preference": 17,
    "single-session-user": 17,
    "single-session-assistant": 17,
    "knowledge-update": 17,
    "multi-session": 16,
    "temporal-reasoning": 16,
}

ZH_PLACEHOLDER = "[待翻译：请只替换本行，保留上下边界标记]"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._") or "unnamed"


def _json_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _sample_score(seed: int, question_type: str, question_id: str) -> str:
    value = f"{seed}:{question_type}:{question_id}".encode("utf-8")
    return _sha256_bytes(value)


def _write_question_answer(path: Path, case: dict, source_index: int) -> None:
    lines = [
        "---",
        f"question_id: {_json_value(case['question_id'])}",
        f"question_type: {_json_value(case['question_type'])}",
        f"question_date: {_json_value(case['question_date'])}",
        f"source_index: {source_index}",
        f"answer_session_ids: {_json_value(case['answer_session_ids'])}",
        "translation_status: TODO",
        "---",
        "# Question and Gold Answer Translation",
        "",
        "> 只编辑两个 `ZH_*` 边界之间的内容。英文、ID、日期、题型和证据 ID 均不可修改。",
        "",
        "## Question",
        "",
        "### English source — DO NOT EDIT",
        "",
        "<!-- SOURCE_QUESTION_BEGIN -->",
        str(case["question"]),
        "<!-- SOURCE_QUESTION_END -->",
        "",
        "### Chinese translation — EDIT HERE",
        "",
        "<!-- ZH_QUESTION_BEGIN -->",
        ZH_PLACEHOLDER,
        "<!-- ZH_QUESTION_END -->",
        "",
        "## Gold answer",
        "",
        "### English source — DO NOT EDIT",
        "",
        "<!-- SOURCE_ANSWER_BEGIN -->",
        str(case["answer"]),
        "<!-- SOURCE_ANSWER_END -->",
        "",
        "### Chinese translation — EDIT HERE",
        "",
        "<!-- ZH_ANSWER_BEGIN -->",
        ZH_PLACEHOLDER,
        "<!-- ZH_ANSWER_END -->",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_session(
    path: Path,
    case: dict,
    session_index: int,
    session_id: str,
    timestamp: str,
    messages: list[dict],
) -> None:
    is_evidence = session_id in set(case["answer_session_ids"])
    lines = [
        "---",
        f"question_id: {_json_value(case['question_id'])}",
        f"session_index: {session_index}",
        f"session_id: {_json_value(session_id)}",
        f"timestamp: {_json_value(timestamp)}",
        f"is_evidence_session: {str(is_evidence).lower()}",
        f"turn_count: {len(messages)}",
        "translation_status: TODO",
        "---",
        f"# Session {session_index:03d} Translation",
        "",
        "> 按 turn 翻译，只编辑 `ZH_TURN_*` 边界内的内容。不要编辑 source、role、has_answer、ID 或时间。",
        "",
    ]
    for turn_index, message in enumerate(messages):
        role = str(message["role"])
        has_answer = message.get("has_answer", "NOT_PRESENT")
        lines.extend(
            [
                f"## Turn {turn_index:03d} — {role}",
                "",
                f"- role: `{role}` — DO NOT EDIT",
                f"- has_answer: `{_json_value(has_answer)}` — DO NOT EDIT",
                "",
                "### English source — DO NOT EDIT",
                "",
                f"<!-- SOURCE_TURN_{turn_index:03d}_BEGIN -->",
                str(message["content"]),
                f"<!-- SOURCE_TURN_{turn_index:03d}_END -->",
                "",
                "### Chinese translation — EDIT HERE",
                "",
                f"<!-- ZH_TURN_{turn_index:03d}_BEGIN -->",
                ZH_PLACEHOLDER,
                f"<!-- ZH_TURN_{turn_index:03d}_END -->",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def _translation_guide() -> str:
    return """# LongMemEval-ZH-v0.1 翻译说明

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
"""


def _workpack_readme(case_count: int, session_count: int, turn_count: int) -> str:
    return f"""# LongMemEval-ZH-v0.1 Translation Workpack

本翻译包包含 {case_count} 个分层样本、{session_count} 个 session、{turn_count} 个 turn。

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
"""


def build(source: Path, output: Path, seed: int) -> None:
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing translation workpack: {output}")

    source_bytes = source.read_bytes()
    data = json.loads(source_bytes.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("LongMemEval source must be a JSON list")

    available = Counter(str(case.get("question_type")) for case in data)
    if set(available) != set(SAMPLE_QUOTAS):
        raise ValueError(f"unexpected question types: {sorted(available)}")

    indexed = list(enumerate(data))
    selected: list[tuple[int, dict]] = []
    for question_type, quota in SAMPLE_QUOTAS.items():
        candidates = [(index, case) for index, case in indexed if case["question_type"] == question_type]
        candidates.sort(key=lambda item: _sample_score(seed, question_type, item[1]["question_id"]))
        if len(candidates) < quota:
            raise ValueError(f"not enough {question_type} cases for quota {quota}")
        selected.extend(candidates[:quota])
    selected.sort(key=lambda item: item[0])

    output.mkdir(parents=True)
    cases_root = output / "cases"
    cases_root.mkdir()

    manifest_cases: list[dict] = []
    structure_cases: list[dict] = []
    index_rows: list[dict] = []
    total_sessions = 0
    total_turns = 0

    for order, (source_index, case) in enumerate(selected, start=1):
        required = {
            "question_id",
            "question_type",
            "question",
            "question_date",
            "answer",
            "answer_session_ids",
            "haystack_dates",
            "haystack_session_ids",
            "haystack_sessions",
        }
        if set(case) != required:
            raise ValueError(f"unexpected schema for case {case.get('question_id')}: {sorted(case)}")
        sessions = case["haystack_sessions"]
        session_ids = case["haystack_session_ids"]
        dates = case["haystack_dates"]
        if not (len(sessions) == len(session_ids) == len(dates)):
            raise ValueError(f"unaligned session arrays for {case['question_id']}")
        missing_evidence = set(case["answer_session_ids"]) - set(session_ids)
        if missing_evidence:
            raise ValueError(f"missing evidence sessions for {case['question_id']}: {sorted(missing_evidence)}")
        for messages in sessions:
            for message in messages:
                if not {"role", "content"}.issubset(message):
                    raise ValueError(f"message missing role/content in {case['question_id']}")
                unexpected_message_keys = set(message) - {"role", "content", "has_answer"}
                if unexpected_message_keys:
                    raise ValueError(
                        f"unexpected message keys in {case['question_id']}: {sorted(unexpected_message_keys)}"
                    )
                if "has_answer" in message and not isinstance(message["has_answer"], bool):
                    raise ValueError(f"non-boolean has_answer in {case['question_id']}")

        case_id = str(case["question_id"])
        case_root = cases_root / _safe_name(case_id)
        sessions_root = case_root / "sessions"
        sessions_root.mkdir(parents=True)
        _write_question_answer(case_root / "question_answer.md", case, source_index)

        locked_sessions: list[dict] = []
        for session_index, (session_id, timestamp, messages) in enumerate(zip(session_ids, dates, sessions)):
            filename = f"session_{session_index:03d}__{_safe_name(str(session_id))}.md"
            _write_session(
                sessions_root / filename,
                case,
                session_index,
                str(session_id),
                str(timestamp),
                messages,
            )
            locked_sessions.append(
                {
                    "session_index": session_index,
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "file": f"cases/{_safe_name(case_id)}/sessions/{filename}",
                    "turns": [
                        {
                            "turn_index": turn_index,
                            "role": message["role"],
                            **(
                                {"has_answer": message["has_answer"]}
                                if "has_answer" in message
                                else {}
                            ),
                            "source_content_sha256": _sha256_bytes(
                                str(message["content"]).encode("utf-8")
                            ),
                        }
                        for turn_index, message in enumerate(messages)
                    ],
                }
            )

        session_count = len(sessions)
        turn_count = sum(len(messages) for messages in sessions)
        evidence_session_count = sum(session_id in set(case["answer_session_ids"]) for session_id in session_ids)
        total_sessions += session_count
        total_turns += turn_count
        manifest_cases.append(
            {
                "order": order,
                "source_index": source_index,
                "question_id": case_id,
                "question_type": case["question_type"],
                "session_count": session_count,
                "turn_count": turn_count,
                "evidence_session_count": evidence_session_count,
            }
        )
        structure_cases.append(
            {
                "source_index": source_index,
                "question_id": case_id,
                "question_type": case["question_type"],
                "question_date": case["question_date"],
                "answer_session_ids": case["answer_session_ids"],
                "question_sha256": _sha256_bytes(str(case["question"]).encode("utf-8")),
                "answer_sha256": _sha256_bytes(str(case["answer"]).encode("utf-8")),
                "sessions": locked_sessions,
            }
        )
        index_rows.append(
            {
                "order": order,
                "question_id": case_id,
                "question_type": case["question_type"],
                "question_answer_file": f"cases/{_safe_name(case_id)}/question_answer.md",
                "session_count": session_count,
                "turn_count": turn_count,
                "translator_status": "TODO",
            }
        )

    manifest = {
        "dataset_name": "LongMemEval-ZH-v0.1-translation-workpack",
        "source_dataset": "LongMemEval-S v1 cleaned",
        "source_path_at_build": str(source.resolve()),
        "source_sha256": _sha256_bytes(source_bytes),
        "source_case_count": len(data),
        "sample_seed": seed,
        "sample_method": "lowest SHA256(seed:question_type:question_id) within each stratum",
        "sample_quotas": SAMPLE_QUOTAS,
        "sample_case_count": len(selected),
        "sample_session_count": total_sessions,
        "sample_turn_count": total_turns,
        "language_target": "zh-CN",
        "history_variant": "full",
        "cases": manifest_cases,
    }
    (output / "sampling_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "structure_lock.json").write_text(
        json.dumps({"cases": structure_cases}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "TRANSLATION_GUIDE.md").write_text(_translation_guide(), encoding="utf-8")
    (output / "README.md").write_text(
        _workpack_readme(len(selected), total_sessions, total_turns),
        encoding="utf-8",
    )
    (output / "GLOSSARY.md").write_text(
        "# Translation Glossary\n\n"
        "在此记录统一译法。建议表格列为：English、中文译法、适用范围、备注。\n\n"
        "| English | 中文译法 | 适用范围 | 备注 |\n"
        "|---|---|---|---|\n",
        encoding="utf-8",
    )
    with (output / "translation_index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(index_rows[0]))
        writer.writeheader()
        writer.writerows(index_rows)

    print(
        json.dumps(
            {
                "output": str(output.resolve()),
                "cases": len(selected),
                "sessions": total_sessions,
                "turns": total_turns,
                "source_sha256": manifest["source_sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260825)
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve(), args.seed)


if __name__ == "__main__":
    main()
