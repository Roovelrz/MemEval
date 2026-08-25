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
