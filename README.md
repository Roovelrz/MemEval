# Memory Eval Pipeline

面向 Agent 记忆系统的评测框架：以冻结的 MemEval-v0.1 复合 benchmark 为核心，
通过可替换的四层 Adapter 驱动 `Dataset -> Memory -> Answer LLM -> Judge LLM -> Trace`
全流程，产出 Trace 报告与静态 HTML Dashboard。最终目标是在同一数据集上对本地的
Memory 系统与本地 LLM 做消融实验。

中文使用手册见 [`USAGE_ZH.md`](USAGE_ZH.md)。

## 框架分层

```text
scripts/run_memeval.py                 # 端到端编排入口
└─ memory_eval/runners/memeval.py      # Runner：只组织流程，不理解具体实现
   ├─ adapters/dataset/  locomo / longmemeval / personamem-v2   # 可替换
   ├─ adapters/memory/   reme / off                              # 可替换
   ├─ adapters/llm/      openai-compatible（Answer/Judge 各自独立配置）# 可替换
   └─ adapters/Trace/    MemEval Trace                            # 框架配套，固定
```

- Dataset / Memory / LLM 三类 Adapter 相互独立，均可在 `registry` 登记新实现后单独替换。
- Trace Adapter 与 MemEval 八维结构绑定，是评测框架自身的产物，不作为实验变量。
- 各层职责与扩展方法见 [`memory_eval/adapters/README.md`](memory_eval/adapters/README.md)，
  Memory 侧系统协议见 [`memory_eval/systems/README.md`](memory_eval/systems/README.md)，
  正式运行说明见 [`memory_eval/runners/README.md`](memory_eval/runners/README.md)。

## 快速开始

前置：Python 3.12，安装依赖并准备好本地 ReMe（见 USAGE_ZH.md）。LLM 密钥只放
被 Git 忽略的 `.env`（自动加载，进程环境变量优先）：

```powershell
DEEPSEEK_API_KEY=<your-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com        # 或本地 OpenAI 兼容 endpoint
DEEPSEEK_MODEL=deepseek-v4-flash
```

冒烟（单维度 1 条，验证链路）：

```powershell
python scripts/run_memeval.py --dimension D02 --limit 1 --run-id smoke-1
```

全量（298 条冻结 case）：

```powershell
python scripts/run_memeval.py --run-id reme-full
```

消融实验矩阵：

```powershell
python scripts/run_memeval.py --memory-adapter reme --run-id reme-full   # 完整记忆系统
python scripts/run_memeval.py --memory-adapter off  --run-id off-full    # 无记忆对照
# LLM 消融：固定 Judge，仅把 DEEPSEEK_* 指向待评测的本地 endpoint
```

`--memory-adapter off` 是无记忆对照组：走完整检索→回答→评审流程，检索指标如实
记 0（而非 unsupported），用于衡量 memory 系统带来的净增益。

## 运行结果布局

结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离（`reme` / `off` 各自成目录）：

- `Detailed Trace Report/`：原始产物与溯源（results.jsonl、retrieval_run_config.json、
  raw 检索响应、`trace/` 下的 per-case Markdown、judge_review、integrity_report 等）。
- `Trace Summary/`：面向人的静态 Dashboard（`Dashboard.html` 直接用浏览器打开，
  无需服务器或 Node 构建）与精简摘要。

`retrieval_run_config.json` 记录了 run 的完整配置（含 memory_adapter、top_k、
selected_case_ids），resume 时会校验配置一致，防止混跑。

## 重建报告（不重跑评测）

Dashboard / Trace 展示逻辑升级后，旧 run 无需重新评测：

```powershell
# 从已持久化产物重建 Trace 与 Dashboard，不重启服务、不调 LLM
python scripts/run_memeval.py --trace-only --run-dir results/memeval_v0_1/reme/<run-id>
```

另有独立工具：`scripts/build_trace_report.py`（仅 Trace）、
`scripts/build_html_report.py`（仅 Dashboard）、
`scripts/organize_result_layout.py --refresh`（刷新已组织 run 的摘要）。

## 阶段独立性

Answer 与 Judge 是独立可续跑的阶段：检索失败则不进入 Answer，Answer 失败则不进入
Judge；失败 case 会与成功输出对账后跳过重跑。历史 LongMemEval / LoCoMo /
PersonaMem 的独立检索、Answer、Judge 脚本（`run_reme_retrieval_eval.py`、
`run_answer_eval.py`、`run_judge_eval.py`、`run_reme_end_to_end_eval.py`）仍保留可用。

## 数据集

MemEval-v0.1：298 条冻结 case，覆盖 D01–D08 八个维度（记忆写入、长期记忆检索、
长时跨会话、主动记忆激活、用户画像、动态更新冲突、超长上下文、隐私与用户隔离），
已通过阶段审计。各维度的构成、来源与指标语义见
[`dataset/MemEval-v0.1/README.md`](dataset/MemEval-v0.1/README.md)
及各维度目录下的 README。case 选择用 `scripts/freeze_memeval_selection.py` 冻结，
保证消融各 arm 完全一致。

## Attribution

- Dataset: [LoCoMo](https://github.com/snap-research/locomo) /
  [LongMemEval](https://github.com/xiaowu0162/LongMemEval) /
  [PersonaMem](https://arxiv.org/abs/2504.14234)
- AML pipeline: [Agent Memory Leaderboard](https://github.com/AML-memory/agent-memory-leaderboard)
