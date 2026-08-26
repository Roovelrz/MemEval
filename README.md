# LongMemEval-S Eval MVP

中文端到端运行、分阶段续跑、参数说明和结果排查见
[`USAGE_ZH.md`](USAGE_ZH.md)。

This first phase implements only:

```text
LongMemEval-S cleaned -> isolated Add -> Search -> AML Answer -> AML Judge -> summary
```

It does not integrate LoCoMo or PersonaMem-v2 and does not modify the upstream AML
answer or judge prompts.

## Local preparation smoke tests

From the `memory_eval_pipeline` repository root:

```powershell
py -3.12 -m memory_eval.cli longmemeval `
  --data ..\LongMemEval\data\longmemeval_s_cleaned.json `
  --mode oracle `
  --limit 1 `
  --top-k 10 `
  --run-id oracle-1 `
  --prepare-only

py -3.12 -m memory_eval.cli longmemeval `
  --data ..\LongMemEval\data\longmemeval_s_cleaned.json `
  --mode memory `
  --limit 1 `
  --top-k 10 `
  --run-id memory-1 `
  --prepare-only
```

`InMemorySessionAdapter` is a lexical smoke adapter. It proves namespace, Add,
Search, and artifact wiring only; it is not a production memory baseline.

## ReMe BM25 retrieval baseline

This path uses the local ReMe clone as a real third-party backend. Each
LongMemEval session is written verbatim to its own Markdown file, ReMe rebuilds
its local index for that case, and `search_step` runs with
`vector_weight=0.0`. The adapter does not enable an LLM, embeddings,
`auto_memory`, `auto_resource`, or `auto_dream`.

With ReMe cloned beside this repository, install the editable package and its
non-Studio core dependencies:

```powershell
py -3.12 -m pip install -e ..\ReMe
py -3.12 -m pip install -r requirements-reme.txt
```

The local ReMe 0.4.1.8 clone pins `reme-ai-studio==0.4.1.8` in its `core`
extra, but that package version was unavailable from the configured package
index during this integration. The BM25 adapter does not use ReMe Studio, so
`requirements-reme.txt` intentionally contains the remaining core
dependencies only.

Run retrieval-only evaluation without AML Answer/Judge:

```powershell
py -3.12 -m memory_eval.cli longmemeval `
  --data ..\LongMemEval\data\longmemeval_s_cleaned.json `
  --mode memory `
  --memory-adapter reme `
  --limit 20 `
  --top-k 10 `
  --run-id reme-20 `
  --prepare-only
```

The run directory contains `prepared.jsonl`, `retrieval.jsonl`,
`summary.json`, and `run_config.json`. The retrieval-only summary reports
Hit@K, Recall@K, average search latency, and failed case IDs. A single
adapter-owned workspace is cleared after every case; no ReMe service, Docker,
Milvus, Qdrant, WSL, or external database is used.

### Standalone configurable runner

For the service-oriented ReMe baseline described in the Retrieval Baseline
plan, use [`scripts/run_reme_retrieval_eval.py`](scripts/run_reme_retrieval_eval.py).
It is independent of the AML Answer/Judge path. The runner reads the frozen
Clean JSON (or a compatible JSONL), creates one ReMe workspace per case, calls
`health_check -> reindex -> search`, maps returned Markdown paths back to
session IDs, deduplicates chunk hits, and writes raw and normalized retrieval
artifacts.

The generated default config is a minimal BM25-only service: it does not start
an LLM or embedding component, so no API key is required. The `--model` option
is only a label in `run_config.json` for this baseline; it does not call a
model. To test a ReMe hybrid or embedding setup, provide a complete custom
config with `--reme-config` and set `--vector-weight` accordingly.

The local executable is not always on `PATH` on Windows. Passing its absolute
path is therefore the most reproducible invocation:

```powershell
py -3.12 scripts/run_reme_retrieval_eval.py `
  --data datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json `
  --cases 1 `
  --top-k 10 `
  --run-id reme-smoke-1 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

Then expand in the recommended order:

```powershell
# five cases
py -3.12 scripts/run_reme_retrieval_eval.py --data <dataset.json> --cases 5 --run-id reme-5

# all selected cases, with a deterministic shuffled order
py -3.12 scripts/run_reme_retrieval_eval.py --data <dataset.json> --cases 0 --shuffle --seed 42 --run-id reme-all
```

Useful switches are `--start`, `--cases/--limit`, `--top-k`,
`--search-multiplier`, `--min-score`, `--base-port`, `--startup-timeout`,
`--keep-workspaces`, and `--reme-config`. Replace `--data` with any JSON/JSONL
dataset whose cases expose `case_id`, `question`, `gold_answer`, and a
`sessions` list; the runner also accepts the original LongMemEval
`haystack_sessions` shape.

Each run is stored below `results/reme_retrieval/<run-id>/`:

- `run_config.json`: dataset, ReMe command/config, baseline switches, and model label.
- `prepared.jsonl`: one normalized case row with retrieved context.
- `retrieval.jsonl`: per-case ranked sessions, raw result count, Hit@K, Recall@K, MRR, and latency.
- `raw_search/`: exact ReMe response for each successful case.
- `failures.jsonl`: case-level startup, indexing, or search failures.
- `summary.json`: aggregate metrics and success/failure counts.
- `workspaces/` and `reme_service.log`: retained only when `--keep-workspaces` is set (the log is always retained).

The first validated smoke run on the frozen `LongMemEval-ZH-20-v0.1` dataset
retrieved its evidence session at rank 1 for case `118b2229` (`Hit@10=1`,
`Recall@10=1`, `MRR=1`). This is a retrieval-only signal, not an answer-quality
or judge result.

## Independent Answer and Judge runners

The retrieval runner stops after producing `prepared.jsonl`. Answer generation
and judging are separate scripts so either stage can be rerun without rebuilding
the ReMe index:

- [`scripts/run_answer_eval.py`](scripts/run_answer_eval.py) reads prepared cases and writes `answers.jsonl`.
- [`scripts/run_judge_eval.py`](scripts/run_judge_eval.py) reads prepared cases plus `answers.jsonl` and writes `scores.jsonl`.

Both use an OpenAI-compatible `/chat/completions` endpoint. By default they
read the following environment variables, so the key itself never appears in
the command line or artifacts:

```powershell
$env:DEEPSEEK_API_KEY = "<your-key>"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
$env:DEEPSEEK_MODEL = "deepseek-v4-flash"
```

The repository-root `.env` is also loaded automatically by these two runners;
existing process environment variables take precedence.

For `deepseek-v4-flash`, the runners calculate USD cost from cache-hit input,
cache-miss input, and output tokens using the auditable built-in DeepSeek price
entry. The three per-million-token rates and a price multiplier can be
overridden independently for Answer and Judge; unknown models remain
`NOT_RECORDED` unless all three rates are supplied.

Run the stages independently:

```powershell
py -3.12 scripts/run_answer_eval.py `
  --input results/reme_retrieval/reme-baseline-20/prepared.jsonl `
  --output results/reme_retrieval/reme-baseline-20/answers.jsonl

py -3.12 scripts/run_judge_eval.py `
  --input results/reme_retrieval/reme-baseline-20/prepared.jsonl `
  --answers results/reme_retrieval/reme-baseline-20/answers.jsonl `
  --output results/reme_retrieval/reme-baseline-20/scores.jsonl
```

Each stage supports `--model`, `--base-url`, the corresponding `*-env`
options, token/timeout/retry controls, `--start`, `--limit`, and
`--overwrite`. Existing output IDs are skipped by default, which makes a
failed run resumable. It also writes `answer_run_config.json`,
`answer_summary.json`, `judge_run_config.json`, `judge_summary.json`, and
stage-specific failure JSONL files. The Judge uses the AML-compatible
CORRECT/WRONG prompt and reports accuracy only for successfully judged rows.

## One-command end-to-end runner

[`scripts/run_reme_end_to_end_eval.py`](scripts/run_reme_end_to_end_eval.py)
orchestrates the three stages in one run. It exposes the ReMe dataset,
workspace, BM25/search, Answer, and Judge settings in one command:

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --data datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json `
  --cases 1 `
  --top-k 10 `
  --run-id reme-e2e-1 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

The orchestrator stops before Answer if Retrieval fails, and stops before
Judge if Answer fails. After the model stages finish, it builds a human-readable
Trace report from the artifacts that are available. It stores
`end_to_end_run_config.json` and `end_to_end_summary.json` alongside
`prepared.jsonl`, `answers.jsonl`, `scores.jsonl`, and all stage reports. Use `--answer-model` or
`--judge-model` to override the environment model for one run; use separate
`--answer-*` and `--judge-*` environment/base-url options when the two stages
use different providers.

## Trace analysis report

Every end-to-end run now writes its primary review output to
`<run-dir>/trace/trace_summary.md`. The report combines Add observability,
Retrieval ranking and evidence checks, Answer context flow, Judge output, four
quadrants, and upstream-first root-cause labels. The supporting files are:

- `trace/trace_index.md`: failure-first links to every case.
- `trace/cases/<case_id>.md`: complete per-case trace and links back to raw artifacts.
- `trace/judge_review.md`: Judge=WRONG, Judge failure, and suspicious-Judge review queue.
- `trace/trace_summary.json`: machine-readable aggregate and per-case classification.

Existing raw artifacts are not changed. Information the earlier runners did not
persist, such as per-session Add acknowledgements, exact sent prompts, and
provider-side truncation, is displayed as `NOT_RECORDED` instead of inferred.
The report also freezes `integrity_report.json`, writes a selected-case
`dataset_validation.json`, reports conditional Answer accuracy and end-to-end
latency, and records Embedding/Extraction as either measured, `NOT_RECORDED`,
or explicitly `NOT_APPLICABLE`. New retrieval runs retain an
`eval_code_snapshot/manifest.json` so a dirty working tree does not hide the
exact runner source used.

To build or rebuild only the report for an existing run, without rerunning ReMe
or calling the Answer/Judge APIs:

```powershell
py -3.12 scripts/build_trace_report.py `
  --run-dir results/reme_end_to_end/reme-e2e-1-fixed
```

Use `--data <dataset.json>` only when the dataset path in `run_config.json` is
missing or no longer valid.

## AML Answer and Judge

Set these environment variables before removing `--prepare-only`:

```text
ANSWER_API_BASE
ANSWER_API_KEY
ANSWER_MODEL
JUDGE_API_BASE
JUDGE_API_KEY
JUDGE_MODEL
```

The CLI then invokes the unchanged upstream AML sibling repository at
`..\AML\agent-memory-leaderboard\data\longmemeval-s\pipeline.py` for answer
generation and binary evaluation. Override this location with `--aml-root`.

## Attribution

- AML pipeline: [Agent Memory Leaderboard](https://github.com/AML-memory/agent-memory-leaderboard)
- Dataset: [LongMemEval](https://github.com/xiaowu0162/LongMemEval)
