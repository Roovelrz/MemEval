# LongMemEval-S Eval MVP

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
