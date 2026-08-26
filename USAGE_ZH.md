# Memory Eval Pipeline 完整使用指南

这套框架当前用于运行下面这条评测链路：

```text
LongMemEval-ZH 数据集
→ ReMe 写入与 BM25 检索
→ prepared.jsonl
→ Answer Model
→ Judge Model
→ Trace 汇总与逐 Case 根因分析
```

最推荐的使用方式是先跑 1 条 case 做 Smoke Test，确认整条链路可用后，再扩大到 5 条和全部 20 条。不要一开始就跑全量。

## 1. 当前默认组件

| 模块 | 当前实现 | 是否调用外部模型 |
| --- | --- | :---: |
| 数据集 | `LongMemEval-ZH-20-v0.1` | 否 |
| Memory / Retrieval | 本地 ReMe，BM25-only | 否 |
| Answer | OpenAI-compatible Chat Completions API | 是 |
| Judge | OpenAI-compatible Chat Completions API | 是 |
| Trace Analysis | 本地 Python 汇总脚本 | 否 |

默认数据集位于：

```text
datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json
```

## 2. 第一次运行前的准备

以下命令均在仓库根目录执行：

```powershell
Set-Location E:\LRZ_Workplace\fork\memory_eval_pipeline
```

### 2.1 安装基础依赖

```powershell
py -3.12 -m pip install -r requirements.txt
```

如需运行测试：

```powershell
py -3.12 -m pip install -r requirements-dev.txt
```

### 2.2 安装本地 ReMe

当前假设 ReMe 已克隆到相邻目录：

```text
E:\LRZ_Workplace\fork\ReMe
```

安装本地包和本项目使用的非 Studio 依赖：

```powershell
py -3.12 -m pip install -e ..\ReMe
py -3.12 -m pip install -r requirements-reme.txt
```

确认 ReMe 命令位置。当前已验证过的路径是：

```text
C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe
```

如果本机位置不同，可以执行：

```powershell
Get-Command reme -ErrorAction SilentlyContinue
```

### 2.3 配置 Answer 和 Judge API

推荐在仓库根目录的 `.env` 中配置。该文件已经被 `.gitignore` 忽略，不会进入 Git：

```dotenv
DEEPSEEK_API_KEY=填写你的API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

也可以只对当前 PowerShell 进程设置：

```powershell
$env:DEEPSEEK_API_KEY = "填写你的API密钥"
$env:DEEPSEEK_BASE_URL = "https://api.deepseek.com"
$env:DEEPSEEK_MODEL = "deepseek-v4-flash"
```

环境变量的优先级高于 `.env`。API Key 不会被写进 `run_config.json` 或 Trace 报告。

## 3. 推荐方式：一条命令运行完整 Eval

### 3.1 先运行 1 条 Smoke Test

每次完整运行都建议使用新的 `run-id`：

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --data datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json `
  --cases 1 `
  --start 0 `
  --top-k 10 `
  --run-id reme-e2e-smoke-1 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

完整流程会依次运行：

```text
Retrieval → Answer → Judge → Trace report
```

只有 Retrieval 成功才会启动 Answer；只有 Answer 成功才会启动 Judge。无论前面是否失败，最后都会尽量根据已有产物生成 Trace。

### 3.2 扩大到 5 条

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --cases 5 `
  --top-k 10 `
  --run-id reme-e2e-5 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

### 3.3 运行冻结数据集中的全部 20 条

`--cases 0` 表示运行从 `--start` 开始的全部 case：

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --cases 0 `
  --top-k 10 `
  --run-id reme-e2e-zh20-v01 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

如需固定随机顺序：

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py `
  --cases 0 `
  --shuffle `
  --seed 42 `
  --run-id reme-e2e-zh20-shuffled `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

## 4. 分阶段运行

分阶段运行适合下面几种情况：

- 只想分析 Retrieval，不想消耗 Answer/Judge API。
- Retrieval 已完成，只想更换 Answer Model。
- Answer 已完成，只想更换 Judge Model。
- 某个 API 阶段中断后，需要从已有 JSONL 继续。

### 4.1 只运行 ReMe Retrieval

```powershell
py -3.12 scripts/run_reme_retrieval_eval.py `
  --data datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json `
  --cases 1 `
  --top-k 10 `
  --run-id reme-retrieval-smoke `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

默认结果目录：

```text
results/reme_retrieval/reme-retrieval-smoke/
```

这个阶段只生成 Retrieval 和 `prepared.jsonl`，不调用 DeepSeek。

### 4.2 对 prepared.jsonl 运行 Answer

```powershell
py -3.12 scripts/run_answer_eval.py `
  --input results/reme_retrieval/reme-retrieval-smoke/prepared.jsonl `
  --output results/reme_retrieval/reme-retrieval-smoke/answers.jsonl
```

Answer runner 默认跳过已经存在于 `answers.jsonl` 中的 case_id，因此中断后可以执行同一命令继续。

切换 Answer Model：

```powershell
py -3.12 scripts/run_answer_eval.py `
  --input results/reme_retrieval/reme-retrieval-smoke/prepared.jsonl `
  --output results/reme_retrieval/reme-retrieval-smoke/answers-new-model.jsonl `
  --model deepseek-v4-flash `
  --max-tokens 4096 `
  --temperature 0
```

建议换模型时写入新的输出文件，避免把不同模型的结果混在一起。

### 4.3 运行 Judge

```powershell
py -3.12 scripts/run_judge_eval.py `
  --input results/reme_retrieval/reme-retrieval-smoke/prepared.jsonl `
  --answers results/reme_retrieval/reme-retrieval-smoke/answers.jsonl `
  --output results/reme_retrieval/reme-retrieval-smoke/scores.jsonl
```

Judge runner 同样会跳过已经存在于 `scores.jsonl` 中的 case_id。

如果选择范围内缺少 Answer，Judge 会直接报错，不会为缺少的 case 伪造分数。

### 4.4 只生成或重新生成 Trace

这个操作不会运行 ReMe，也不会调用 Answer/Judge API：

```powershell
py -3.12 scripts/build_trace_report.py `
  --run-dir results/reme_end_to_end/reme-e2e-1-fixed
```

如果 `run_config.json` 中没有有效的数据集路径，再显式指定：

```powershell
py -3.12 scripts/build_trace_report.py `
  --run-dir results/reme_end_to_end/reme-e2e-1-fixed `
  --data datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1/dataset.json
```

重新生成 Trace 只会更新 `<run-dir>/trace/` 中的分析报告，不会改写 `retrieval.jsonl`、`prepared.jsonl`、`answers.jsonl` 或 `scores.jsonl`。

## 5. 常用参数

### 数据与范围

| 参数 | 作用 |
| --- | --- |
| `--data` | 更换数据集 JSON/JSONL |
| `--cases N` | 运行 N 条；`0` 表示全部 |
| `--start N` | 从第 N 条开始，默认 0 |
| `--shuffle` | 在截取 case 前打乱 |
| `--seed 42` | 固定随机顺序 |
| `--run-id` | 本次运行目录名，建议每次唯一 |
| `--output-dir` | 更换结果根目录 |

### Retrieval

| 参数 | 作用 |
| --- | --- |
| `--top-k 10` | 最终送入 Answer 的 session 数 |
| `--search-multiplier 3` | ReMe 原始候选数约为 `top_k × multiplier` |
| `--min-score 0.0` | ReMe 最低检索分数 |
| `--base-port 23330` | 第一个临时 ReMe 服务端口 |
| `--startup-timeout 60` | 等待 ReMe 服务启动的秒数 |
| `--reme-cmd` | ReMe 可执行文件路径或命令 |
| `--reme-config` | 使用自定义 ReMe 配置 |
| `--vector-weight 0.0` | `0.0` 是当前 BM25 baseline |
| `--keep-workspaces` | 保留每条 case 的临时 ReMe workspace，便于调试但占空间 |

当前 baseline 不启用 embedding、LLM、auto-memory、auto-resource 或 auto-dream。若把 `vector-weight` 改为非 0，应同时提供真正可用的自定义 ReMe 配置，不能只改一个数值。

### Answer / Judge

| 参数 | 作用 |
| --- | --- |
| `--answer-model` / `--judge-model` | 在完整 runner 中分别覆盖模型 |
| `--answer-max-tokens` / `--judge-max-tokens` | 最大输出 token，默认 4096 |
| `--answer-temperature` / `--judge-temperature` | 温度，默认 0 |
| `--answer-timeout` / `--judge-timeout` | 单次请求超时，默认 120 秒 |
| `--answer-retries` / `--judge-retries` | 失败重试次数，默认 3 |
| `--base-url` / `--model` | 在独立 runner 中覆盖 API 地址或模型 |
| `--start` / `--limit` | 在独立 Answer/Judge runner 中选择行范围 |
| `--overwrite` | 删除该阶段已有输出后重跑；会失去该输出文件中的旧结果，谨慎使用 |

## 6. 结果目录怎么读

一次完整运行的目录结构大致如下：

```text
results/reme_end_to_end/<run-id>/
├── run_config.json
├── end_to_end_run_config.json
├── reme_bm25.yaml
├── reme_service.log
├── retrieval.jsonl
├── prepared.jsonl
├── answers.jsonl
├── scores.jsonl
├── failures.jsonl
├── answer_failures.jsonl
├── judge_failures.jsonl
├── summary.json
├── answer_summary.json
├── judge_summary.json
├── end_to_end_summary.json
├── raw_search/
└── trace/
    ├── trace_summary.md
    ├── trace_summary.json
    ├── trace_index.md
    ├── judge_review.md
    └── cases/
        └── <case_id>.md
```

部分 failure 文件只有发生失败时才会出现。

建议按以下顺序查看：

1. `trace/trace_summary.md`：面向人的总结果和主要瓶颈。
2. `trace/trace_index.md`：按失败优先级找到具体 case。
3. `trace/cases/<case_id>.md`：查看 Add → Retrieval → Answer → Judge 完整链路。
4. `trace/judge_review.md`：人工复核 Judge=WRONG、Judge 失败或疑似误判。
5. 最后才查看 JSONL、raw_search 和日志，作为溯源材料。

## 7. 四象限和 Root Cause 怎么看

| 象限 | Retrieval | Answer | 解释 |
| --- | :---: | :---: | --- |
| A | ✓ | ✓ | Memory 找对，Answer 也答对 |
| B | ✗ | ✗ | 优先排查检索召回和排序 |
| C | ✓ | ✗ | 排查上下文丢失、Answer 推理或 Judge |
| D | ✗ | ✓ | 可能靠模型先验猜对，不能证明 Memory 有效 |

自动根因按照真实链路从上游向下判断：

```text
ADD_FAILURE
→ RETRIEVAL_MISS / RETRIEVAL_PARTIAL / RETRIEVAL_LOW_RANK
→ CONTEXT_LOSS
→ ANSWER_FAILURE
→ JUDGE_SUSPECT
→ PASS
```

如果某个字段没有被旧 runner 持久化，Trace 会显示 `NOT_RECORDED`，不会把推测当成事实。

## 8. 退出码与失败排查

| 现象 | 含义与下一步 |
| --- | --- |
| Exit code 0 | 本次执行的全部阶段成功 |
| Exit code 2 | 至少一个 case 或阶段失败；先看各 `*_summary.json` 和 failure JSONL |
| Python traceback / Exit code 1 | 通常是参数、文件、依赖或配置错误，先看最后一行异常 |
| ReMe 启动失败 | 检查 `--reme-cmd`、端口和 `reme_service.log` |
| Answer 内容为空 | 查看 `answer_failures.jsonl`，再用独立 Answer runner 续跑 |
| Judge 格式异常 | 查看 `judge_failures.jsonl` 中保留的 `judge_response` |
| Trace 显示 `NOT_RECORDED` | 原始 runner 未保存该观测字段，不等于该步骤一定失败 |

不要因为总 runner 返回非 0 就只看终端最后一行。首先打开 `trace_summary.md`，再沿失败 case 的 Trace 从 Add 向 Judge 逐层排查。

## 9. 继续运行与重新运行的边界

- Answer 和 Judge 独立 runner 默认支持按 case_id 续跑。
- 完整端到端 runner 会重新执行 Retrieval，因此建议始终使用新的 `run-id`。
- 切换数据集、Retrieval 配置、Answer Model 或 Judge Model 时，也应使用新的 `run-id` 或新的输出文件。
- 不要手工修改旧 run 的 JSONL 后再与新结果比较。
- 对同一轮横向比较，应固定数据集版本、case 顺序、TopK、Answer Model、Judge Model 和 Prompt。

## 10. 开发后自检

运行全部本地测试：

```powershell
py -3.12 -m pytest -q
```

只验证 Trace 报告：

```powershell
py -3.12 -m pytest tests/test_trace_report.py -q
```

查看所有脚本的实时参数说明：

```powershell
py -3.12 scripts/run_reme_end_to_end_eval.py --help
py -3.12 scripts/run_reme_retrieval_eval.py --help
py -3.12 scripts/run_answer_eval.py --help
py -3.12 scripts/run_judge_eval.py --help
py -3.12 scripts/build_trace_report.py --help
```
