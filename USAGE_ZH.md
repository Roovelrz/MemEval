# Memory Eval Pipeline 完整使用指南

当前推荐的评测链路是 MemEval-v0.1 复合 benchmark（298 条冻结 case，八个维度）：

```text
MemEval-v0.1（D01–D08）
→ Memory Adapter（reme 完整系统 / off 无记忆对照）
→ Answer Model
→ Judge Model
→ Trace 汇总与逐 Case 根因分析
→ HTML Dashboard 静态展示
```

最推荐的使用方式是先跑 1 条 case 做 Smoke Test，确认整条链路可用后，再扩大到
单维度全量，最后跑全量。不要一开始就跑 298 条。

历史 LongMemEval-ZH 单数据集链路仍保留，见文末附录。

## 1. 当前默认组件

| 模块 | 当前实现 | 是否调用外部模型 |
| --- | --- | :---: |
| 数据集 | `MemEval-v0.1`（冻结，D01–D08） | 否 |
| Memory / Retrieval | 本地 ReMe（BM25 baseline）或 `off` 无记忆对照 | 否 |
| Answer | OpenAI-compatible Chat Completions API | 是 |
| Judge | OpenAI-compatible Chat Completions API | 是 |
| Trace Analysis | 本地 Python 汇总脚本 | 否 |
| HTML Dashboard | 本地静态 Reporter | 否 |

数据集位于 `dataset/MemEval-v0.1/`；维度构成与指标语义见其 README。

## 2. 第一次运行前的准备

以下命令均在仓库根目录执行：

```powershell
Set-Location E:\LRZ_Workplace\fork\memory_eval_pipeline
```

### 2.1 安装基础依赖

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install -r requirements-dev.txt   # 如需运行测试
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

`--memory-adapter off` 的无记忆对照不启动任何 ReMe 服务，无需此步。

### 2.3 配置 Answer 和 Judge API

推荐在仓库根目录的 `.env` 中配置。该文件已经被 `.gitignore` 忽略，不会进入 Git：

```dotenv
DEEPSEEK_API_KEY=填写你的API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

指向本地 OpenAI 兼容 endpoint（如 vLLM / 公司内网推理服务）时，替换
`DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL` 即可。环境变量的优先级高于 `.env`；
API Key 不会被写进 run 配置或 Trace 报告。

消融实验时务必固定 Judge，只切换 Answer 模型，否则 Judge 偏差会污染结论。

## 3. 运行 MemEval

### 3.1 先运行 1 条 Smoke Test

```powershell
python scripts/run_memeval.py `
  --dimension D02 `
  --limit 1 `
  --run-id smoke-1 `
  --reme-cmd "C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe"
```

完整流程依次运行 `Retrieval → Answer → Judge → Trace → Dashboard`。只有
Retrieval 成功才进入 Answer，只有 Answer 成功才进入 Judge。

### 3.2 扩大到单维度全量

```powershell
python scripts/run_memeval.py --dimension D02 --run-id reme-d02-full
```

`--dimension` 可重复传入以运行多个维度。

### 3.3 全量 298 条

```powershell
python scripts/run_memeval.py --run-id reme-full
```

### 3.4 消融实验矩阵

```powershell
# 完整记忆系统
python scripts/run_memeval.py --memory-adapter reme --run-id reme-full

# 无记忆对照：走完整流程，检索指标如实记 0
python scripts/run_memeval.py --memory-adapter off --run-id off-full

# LLM 消融：固定 Judge，把 .env 指向待评测的本地 endpoint
```

各 arm 的 case 集合由冻结数据集决定，天然一致；不要混用 `--limit`/`--dimension`
造出不同的 case 子集再横向比较。

### 3.5 重建旧 Run 的报告（不重跑评测）

Dashboard / Trace 展示逻辑升级后，旧 run 无需重新评测：

```powershell
python scripts/run_memeval.py --trace-only --run-dir results/memeval_v0_1/reme/<run-id>
```

该命令从已持久化的 `results.jsonl` 重建 Trace 与 Dashboard，会先回填 D03/D06
等派生指标，不重启 ReMe、不调 Answer/Judge API。

## 4. MemEval 常用参数

### 数据与范围

| 参数 | 作用 |
| --- | --- |
| `--data` | 显式指定 MemEval release 目录（默认用内置冻结数据集） |
| `--dimension D02` | 只运行指定维度，可重复传入 |
| `--limit N` | 每个维度最多运行 N 条 |
| `--run-id` | 本次运行目录名，建议每次唯一 |
| `--output-dir` | 更换结果根目录（默认 `results/`） |
| `--memory-adapter reme/off` | 被测 memory 系统；`off` 为无记忆消融对照 |

### Retrieval

| 参数 | 作用 |
| --- | --- |
| `--top-k 10` | 最终送入 Answer 的记忆条数 |
| `--search-multiplier` | ReMe 原始候选数约为 `top_k × multiplier` |
| `--min-score 0.0` | ReMe 最低检索分数 |
| `--reme-cmd` | ReMe 可执行文件路径或命令 |
| `--reme-config` | 使用自定义 ReMe 配置 |
| `--vector-weight 0.0` | `0.0` 是当前 BM25 baseline；非 0 需提供可用配置 |
| `--reme-startup-timeout` | 等待 ReMe 服务启动的秒数 |

Resume 语义：同一 `run-id` 续跑时会校验 `retrieval_run_config.json` 与本次参数
一致（旧 run 缺少 `memory_adapter` 字段时按 `reme` 解释），防止混跑。

### 结果目录怎么读

结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离，`reme` 与 `off` 各自成
目录。目录内部结构与附录的 LongMemEval run 相同（`Detailed Trace Report/` 与
`Trace Summary/`），查看顺序、四象限与 Root Cause 读法、退出码排查、续跑边界
全部沿用第 6–9 节。

## 5. 四象限和 Root Cause 怎么看

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

如果某个字段没有被旧 runner 持久化，Trace 会显示 `NOT_RECORDED`，不会把推测
当成事实。

## 6. 退出码与失败排查

| 现象 | 含义与下一步 |
| --- | --- |
| Exit code 0 | 本次执行的全部阶段成功 |
| Exit code 2 | 至少一个 case 或阶段失败；先看各 `*_summary.json` 和 failure JSONL |
| Python traceback / Exit code 1 | 通常是参数、文件、依赖或配置错误，先看最后一行异常 |
| ReMe 启动失败 | 检查 `--reme-cmd`、端口和 `reme_service.log` |
| Answer 内容为空 | 查看 `answer_failures.jsonl`，检查 API 余额与 endpoint |
| Judge 格式异常 | 查看 `judge_failures.jsonl` 中保留的 `judge_response` |
| Trace 显示 `NOT_RECORDED` | 原始 runner 未保存该观测字段，不等于该步骤一定失败 |

不要因为总 runner 返回非 0 就只看终端最后一行。首先打开 `trace_summary.md`，
再沿失败 case 的 Trace 从 Add 向 Judge 逐层排查。

## 7. 继续运行与重新运行的边界

- Answer 和 Judge 阶段支持按 case_id 续跑，中断后执行同一命令继续。
- 切换 `--memory-adapter`、数据集、Retrieval 配置、Answer Model 或 Judge Model
  时，使用新的 `--run-id`。
- 不要手工修改旧 run 的 JSONL 后再与新结果比较。
- 横向比较时固定：数据集版本、case 顺序、TopK、Answer Model、Judge Model、Prompt。

## 8. 开发后自检

运行全部本地测试：

```powershell
py -3.12 -m pytest -q
```

查看实时参数说明：

```powershell
python scripts/run_memeval.py --help
```

## 附录：历史 LongMemEval-ZH 链路

单数据集时代的独立脚本仍可用，分阶段运行时适合只跑检索或只换 Answer/Judge 模型：

- `scripts/run_reme_retrieval_eval.py`：只跑 ReMe 检索，产出 `prepared.jsonl`，
  不调用 LLM。结果在 `results/reme_retrieval/<run-id>/`。
- `scripts/run_answer_eval.py`：对 `prepared.jsonl` 生成 `answers.jsonl`，按
  case_id 续跑；换模型建议写入新输出文件。
- `scripts/run_judge_eval.py`：读 prepared + answers 产出 `scores.jsonl`；缺
  Answer 的 case 会报错而非伪造分数。
- `scripts/run_reme_end_to_end_eval.py`：LongMemEval/LoCoMo/PersonaMem 的一条
  命令端到端编排，支持 `--cases`/`--start`/`--shuffle`/`--seed`。
- `scripts/build_trace_report.py` / `scripts/build_html_report.py` /
  `scripts/organize_result_layout.py`：单独重建 Trace、Dashboard 或迁移旧平铺
  结果目录。

LLM Cost 说明：`deepseek-v4-flash` 默认使用 DeepSeek 官方价格（Cache Hit
`$0.0028`、Cache Miss `$0.14`、Output `$0.28`，每百万 Token，核对日期
2026-08-26），可通过 `--answer-*-price` / `--judge-*-price` 与 multiplier 覆盖；
非内置模型必须同时提供三种价格，否则 Cost 保持 `NOT_RECORDED`。

结果目录阅读顺序（对 MemEval 与历史 run 均适用）：

1. `Trace Summary/Dashboard.html`：最外层可视化入口。
2. `Trace Summary/summary.json`：高信号 Run 指标。
3. `Trace Summary/trace_summary.md`：可审阅、可复制的中文总报告。
4. `Detailed Trace Report/trace/trace_index.md`：按失败优先级找到具体 case。
5. `Detailed Trace Report/trace/cases/<case_id>.md`：查看完整链路。
6. `Detailed Trace Report/trace/judge_review.md`：人工复核 Judge 结果。
7. 最后才查看 JSONL、raw_search 和日志，作为溯源材料。

`eval_code_snapshot/` 保存本次实际使用的 Runner/Report Python 源码及 SHA-256
manifest，即使 Git 工作区为 dirty 也能确认当时运行的准确代码。
