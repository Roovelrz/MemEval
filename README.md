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
  --workers 2 `
  --top-k 10 `
  --run-id reme-smoke-1 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

Then expand in the recommended order:

```powershell
# five cases; two isolated ReMe services are safe for the current local laptop
py -3.12 scripts/run_reme_retrieval_eval.py --data <dataset.json> --cases 5 --workers 2 --run-id reme-5

# server example; raise Retrieval independently after checking server RAM/CPU
py -3.12 scripts/run_reme_retrieval_eval.py --data <dataset.json> --cases 0 --workers 8 --shuffle --seed 42 --run-id reme-all
```

Useful switches are `--start`, `--cases/--limit`, `--top-k`,
`--search-multiplier`, `--min-score`, `--base-port`, `--startup-timeout`,
`--workers/--retrieval-workers`, `--keep-workspaces`, and `--reme-config`.
Each Retrieval worker starts an isolated ReMe service with a distinct port,
workspace, raw artifact path, and log. Results are still written in selected-case
order. The standalone runner defaults to `1` for backward compatibility; the
end-to-end runner defaults to `2` for a conservative local-laptop profile.
Replace `--data` with any JSON/JSONL
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
- `workspaces/`: retained only when `--keep-workspaces` is set.
- `reme_service_logs/`: one retained service log per case, including parallel runs.

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

Answer and Judge default to `8192` output tokens. If a caller explicitly uses
a smaller value and the provider returns an empty response with
`finish_reason=length`, the shared client performs one recovery attempt at
`8192` tokens. Resumable runs reconcile `answer_failures.jsonl` and
`judge_failures.jsonl` against successful output IDs, while `api_errors.jsonl`
remains an append-only attempt history for provenance.

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
# 中文本地化 20 条；--cases 0 也会运行该注册数据集的全部 20 条
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --dataset LongMemEval-ZH-20-v0.1 `
  --cases 20 `
  --top-k 10 `
  --run-id reme-longmemeval-zh20

# 英文官方原版；先 smoke，再把 --cases 改为 20 或 0（全量 500）
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --dataset LongMemEval-EN-Full `
  --cases 1 `
  --top-k 10 `
  --run-id reme-longmemeval-en-smoke
```

The end-to-end runner uses the local-safe defaults Retrieval `2`, Answer `4`,
and Judge `4`. Override them independently with `--retrieval-workers`,
`--answer-workers`, and `--judge-workers`; use `1` to restore sequential
behavior for any stage. Standalone runners preserve sequential behavior by
default and expose `--workers`, for example:

```powershell
py -3.12 scripts/run_answer_eval.py --input <prepared.jsonl> --output <answers.jsonl> --workers 4
py -3.12 scripts/run_judge_eval.py --input <prepared.jsonl> --answers <answers.jsonl> --output <scores.jsonl> --workers 4
```

Suggested starting profiles:

```powershell
# Local i5 / 16 GB / integrated graphics: BM25 Retrieval is CPU/RAM bound
py -3.12 scripts/run_reme_end_to_end_eval.py --dataset LongMemEval-EN-Full --cases 20 --retrieval-workers 2 --answer-workers 4 --judge-workers 4

# Server starting point; benchmark 20 cases before increasing Retrieval to 8
py -3.12 scripts/run_reme_end_to_end_eval.py --dataset LongMemEval-EN-Full --cases 100 --retrieval-workers 4 --answer-workers 8 --judge-workers 8
```

注册信息位于 `datasets/registry.json`。当前实际接入
`LongMemEval-EN-Full` 和 `LongMemEval-ZH-20-v0.1`；LoCoMo 与 PersonaMem
仅预留、不会被 runner 误当成可运行数据。旧的 `--data <path>` 命令仍然可用。
未显式设置 `--output-dir` 时，结果自动隔离到
`results/en_full/reme/<run-id>/` 或 `results/zh_localized/reme/<run-id>/`。

The orchestrator stops before Answer if Retrieval fails, and stops before
Judge if Answer fails. After the model stages finish, it builds a human-readable
Trace report and a local static HTML dashboard from the artifacts that are available. Every Run
ends with two top-level folders: `Detailed Trace Report/` contains raw/provenance
artifacts, while `Trace Summary/` contains the self-contained dashboard and concise
human-facing summaries. Use `--answer-model` or
`--judge-model` to override the environment model for one run; use separate
`--answer-*` and `--judge-*` environment/base-url options when the two stages
use different providers.

## Trace analysis report

Every end-to-end run keeps its complete Markdown analysis at
`<run-dir>/Detailed Trace Report/trace/trace_summary.md`. The report combines Add observability,
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

For an already organized Run that was resumed from `Detailed Trace Report`,
refresh its concise summary and Dashboard in place after rebuilding Trace:

```powershell
py -3.12 scripts/organize_result_layout.py `
  --run-dir results/en_full/reme/<run-id> `
  --refresh
```

Use `--data <dataset.json>` only when the dataset path in `run_config.json` is
missing or no longer valid.

## Static HTML dashboard

The end-to-end runner writes the primary visual entry point to
`<run-dir>/Trace Summary/Dashboard.html`. This direct entry point opens the files
under `Trace Summary/Dashboard/`, while the dashboard reuses
`Detailed Trace Report/trace/trace_summary.json`
and `trace/cases/*.json`; it never re-runs Eval, Judge, or root-cause logic and
does not mutate source Trace artifacts. It includes aggregate metrics, the
interactive Retrieval × Answer quadrant, capability/pipeline/failure pages,
filterable case tables, full per-case Trace, latency, API stability, token/cost,
run metadata, and optional version comparison.
Dashboard 首页还会从现有结果中选择每个 Dataset case 数最多、时间最新的
Run，展示“Benchmark 表现”；顶部 Benchmark 下拉框会跳转到另一套完整
Dashboard，因此四象限、Case Trace、流程观测和性能页面会一起切换。

To rebuild only the dashboard after Trace already exists:

```powershell
py -3.12 scripts/build_html_report.py `
  --run-dir "results/reme_end_to_end/<run-id>/Detailed Trace Report" `
  --output-dir "results/reme_end_to_end/<run-id>/Trace Summary/Dashboard"
```

To migrate an older flat Run once, use:

```powershell
py -3.12 scripts/organize_result_layout.py `
  --run-dir results/reme_end_to_end/<run-id>
```

Open `Trace Summary/Dashboard.html` directly in a browser. All CSS, JavaScript, and links
are relative, so no server or Node build is required. Missing observations stay
visible as `NOT_RECORDED` rather than being inferred.

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
