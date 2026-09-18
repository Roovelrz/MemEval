# Memory Eval Pipeline 使用指南

当前评测链路：MemEval-v0.1（298 条冻结 case，D01–D08）经 Memory / Answer / Judge 后汇总为
Trace 与 HTML Dashboard。**先跑 1 条 Smoke Test 验证链路，再扩到单维度，最后全量**，不要一
开始跑 298 条。历史 LongMemEval-ZH 单数据集链路见文末附录。

## 1. 默认组件

| 模块 | 实现 | 调外部模型 |
| --- | --- | :---: |
| 数据集 | `MemEval-v0.1`（冻结，D01–D08） | 否 |
| Memory | 本地 ReMe（BM25）或 `off` 无记忆对照 | 否 |
| Answer | OpenAI-compatible Chat Completions API | 是 |
| Judge | OpenAI-compatible Chat Completions API | 是 |
| Trace / Dashboard | 本地 Python 汇总 | 否 |

维度构成与指标语义见 `dataset/MemEval-v0.1/README.md`。

## 2. 第一次运行前的准备

命令均在仓库根目录执行。

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pip install -r requirements-dev.txt   # 如需测试
```

ReMe 已克隆到相邻目录（`E:\LRZ_Workplace\fork\ReMe`），装包并确认命令路径（已验证：
`C:\Users\liruizhi\AppData\Local\Programs\Python\Python312\Scripts\reme.exe`）；`off` 对照无需 ReMe。

```powershell
py -3.12 -m pip install -e ..\ReMe
py -3.12 -m pip install -r requirements-reme.txt
```

配置 API（推荐 `.env`，已被 `.gitignore` 忽略）：

```dotenv
DEEPSEEK_API_KEY=填写你的API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

指向本地 endpoint（vLLM / 内网推理）时替换 `BASE_URL`/`MODEL` 即可；环境变量优先级高于
`.env`。**消融实验务必固定 Judge，只切换 Answer**，否则 Judge 偏差污染结论。

## 3. 运行 MemEval

```powershell
# 冒烟：验证链路
python scripts/run_memeval.py --dimension D02 --limit 1 --run-id smoke-1
# 单维度全量（--dimension 可重复）
python scripts/run_memeval.py --dimension D02 --run-id reme-d02-full
# 全量 298 条
python scripts/run_memeval.py --run-id reme-full
# 消融
python scripts/run_memeval.py --memory-adapter reme --run-id reme-full    # 完整记忆系统
python scripts/run_memeval.py --memory-adapter off  --run-id off-full     # 无记忆对照
```

完整流程依次 `Retrieval → Answer → Judge → Trace → Dashboard`，仅上游成功才进入下游。各维度
case 集合由冻结数据集决定，天然一致；不要用 `--limit`/`--dimension` 造不同 case 子集再比较。

**重建旧 Run（不重跑评测）**：展示逻辑升级后，用已持久化的 `results.jsonl` 重建 Trace 与
Dashboard（会先回填 D03/D06 派生指标，不重启 ReMe、不调 LLM）：

```powershell
python scripts/run_memeval.py --trace-only --run-dir results/memeval_v0_1/reme/<run-id>
```

## 4. 常用参数

| 参数 | 作用 |
| --- | --- |
| `--data` | 显式指定 MemEval release 目录（默认冻结数据集） |
| `--dimension` | 只跑指定维度，可重复传入 |
| `--limit N` | 每个维度最多 N 条 |
| `--run-id` | 运行目录名，建议每次唯一 |
| `--output-dir` | 更换结果根目录（默认 `results/`） |
| `--memory-adapter reme/off` | 被测 memory 系统；`off` 为无记忆消融对照 |
| `--top-k 10` | 送入 Answer 的记忆条数 |
| `--search-multiplier` | ReMe 原始候选数 ≈ `top_k × multiplier` |
| `--min-score 0.0` | ReMe 最低检索分数 |
| `--reme-cmd` / `--reme-config` | ReMe 可执行命令 / 自定义配置 |
| `--vector-weight 0.0` | `0.0` 为当前 BM25 baseline；非 0 需可用配置 |
| `--reme-startup-timeout` | 等待 ReMe 服务启动秒数 |

Resume：同一 `run-id` 续跑会校验 `retrieval_run_config.json` 与本次参数一致，防止混跑。

结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离（reme / off 各自成目录），内部结构、
四象限/根因读法、退出码、续跑边界同第 5–7 节。

## 5. 四象限与根因

| 象限 | Retrieval | Answer | 解释 |
| :--: | :---: | :---: | --- |
| A | ✓ | ✓ | Memory 找对，Answer 也答对 |
| B | ✗ | ✗ | 优先排查检索召回和排序 |
| C | ✓ | ✗ | 排查上下文丢失、Answer 推理或 Judge |
| D | ✗ | ✓ | 可能靠模型先验猜对，不能证明 Memory 有效 |

根因按真实链路向上游判断：`ADD_FAILURE → RETRIEVAL_MISS/PARTIAL/LOW_RANK → CONTEXT_LOSS →
ANSWER_FAILURE → JUDGE_SUSPECT → PASS`。未持久化的字段显示 `NOT_RECORDED`，不当作事实。

## 6. 退出码与排查

| 现象 | 含义与下一步 |
| --- | --- |
| Exit code 0 | 全部阶段成功 |
| Exit code 2 | 至少一个 case/阶段失败；先看各 `*_summary.json` 与 failure JSONL |
| traceback / Exit code 1 | 参数/文件/依赖/配置错误，看最后一行异常 |
| ReMe 启动失败 | 检查 `--reme-cmd`、端口、`reme_service.log` |
| Answer 为空 | 看 `answer_failures.jsonl`，检查 API 余额与 endpoint |
| Judge 格式异常 | 看 `judge_failures.jsonl` 的 `judge_response` |
| `NOT_RECORDED` | runner 未保存该观测，不等于失败 |

不要只看终端最后一行；先开 `trace_summary.md`，再沿失败 case 从 Add 向 Judge 排查。

## 7. 续跑与重跑边界

- Answer / Judge 按 case_id 续跑，中断后重跑同一命令继续。
- 切换 memory-adapter、数据集、Retrieval 配置、Answer/Judge 模型时用新 `--run-id`。
- 不手工改旧 run 的 JSONL 后再与新车相比。横向比较固定：数据集版本、case 顺序、TopK、
  Answer/Judge 模型、Prompt。

## 8. 自检

```powershell
py -3.12 -m pytest -q
python scripts/run_memeval.py --help
```

## 附录：历史 LongMemEval-ZH 链路

单数据集独立脚本仍可用，适合只跑检索或只换模型：

- `scripts/run_reme_retrieval_eval.py`：只跑检索，产出 `prepared.jsonl`，不调 LLM。
- `scripts/run_answer_eval.py`：对 `prepared.jsonl` 生成 `answers.jsonl`，按 case_id 续跑。
- `scripts/run_judge_eval.py`：读 prepared + answers 产出 `scores.jsonl`；缺 Answer 会报错。
- `scripts/run_reme_end_to_end_eval.py`：一条命令端到端，支持 `--cases/--start/--shuffle/--seed`。
- `scripts/build_*.py` / `organize_result_layout.py`：单独重建 Trace / Dashboard / 迁移目录。

LLM Cost：`deepseek-v4-flash` 默认官方价（Cache Hit `$0.0028`、Miss `$0.14`、Out `$0.28`/百万
Token，核对 2026-08-26），可用 `--*-price` 与 multiplier 覆盖；非内置模型须提供三种价格，否则
Cost 显示 `NOT_RECORDED`。

结果阅读顺序：`Trace Summary/Dashboard.html` → `summary.json` → `trace_summary.md` →
`Detailed Trace Report/trace_index.md` → `cases/<case_id>.md` → `judge_review.md` → 最后才看
JSONL / raw_search / 日志溯源。`eval_code_snapshot/` 保存当次运行的源码与 SHA-256 manifest，
即便工作区 dirty 也能确认当时运行的准确代码。