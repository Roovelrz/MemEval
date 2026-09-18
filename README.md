# Memory Eval Pipeline

面向 Agent 记忆系统的评测框架：以冻结的 MemEval-v0.1（298 条 case，D01–D08）为核心，
经四层可替换 Adapter 驱动 `Dataset → Memory → Answer → Judge → Trace`，产出 Trace 报告
与静态 HTML Dashboard，用于在同一数据集上对本地 Memory 系统 / 本地 LLM 做消融。
中文使用手册见 [`USAGE_ZH.md`](USAGE_ZH.md)。

## 框架分层

```text
scripts/run_memeval.py              # 端到端编排入口
└─ memory_eval/runners/memeval.py   # Runner：只组织流程
   ├─ adapters/dataset/  locomo / longmemeval / personamem-v2   # 可替换
   ├─ adapters/memory/   reme / off                              # 可替换
   ├─ adapters/llm/      openai-compatible（Answer/Judge 独立配置）# 可替换
   └─ adapters/Trace/    MemEval Trace                            # 框架配套，固定
```

- Dataset / Memory / LLM Adapter 相互独立，可在 `registry` 登记后单独替换；Trace Adapter 与
  八维结构绑定，不作为实验变量。
- 各层职责见 [`memory_eval/adapters/README.md`](memory_eval/adapters/README.md)，
  系统协议见 [`memory_eval/systems/README.md`](memory_eval/systems/README.md)，
  运行说明见 [`memory_eval/runners/README.md`](memory_eval/runners/README.md)。

## 快速开始

前置：Python 3.12 + 本地记忆系统（以 ReMe 为例，<https://github.com/agentscope-ai/ReMe>）。
LLM 密钥只放被 Git 忽略的 `.env`（进程环境变量优先）：

```powershell
DEEPSEEK_API_KEY=<your-key>
DEEPSEEK_BASE_URL=https://api.deepseek.com        # 或本地 OpenAI 兼容 endpoint
DEEPSEEK_MODEL=deepseek-v4-flash
```

```powershell
python scripts/run_memeval.py --dimension D02 --limit 1 --run-id smoke-1   # 冒烟：验证链路
python scripts/run_memeval.py --run-id reme-full                            # 全量：298 条
# 消融实验矩阵：
python scripts/run_memeval.py --memory-adapter reme --run-id reme-full      # 完整记忆系统
python scripts/run_memeval.py --memory-adapter off  --run-id off-full       # 无记忆对照
```

`--memory-adapter off` 走完整流程但检索指标如实记 0（而非 unsupported），衡量 memory 系统净增益。

## 运行结果布局

结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离（reme / off 各自成目录）：

- `Detailed Trace Report/`：原始产物与溯源（results.jsonl、retrieval_run_config.json、
  raw 检索响应、`trace/` per-case Markdown、judge_review、integrity_report 等）。
- `Trace Summary/`：静态 Dashboard（`Dashboard.html` 直接浏览器打开，无需服务器或 Node）
  与精简摘要。

`retrieval_run_config.json` 记录 run 完整配置（memory_adapter、top_k、selected_case_ids），
resume 时校验配置一致，防止混跑。

## 重建报告（不重跑评测）

展示逻辑升级后，旧 run 无需重新评测：

```powershell
python scripts/run_memeval.py --trace-only --run-dir results/memeval_v0_1/reme/<run-id>
```

独立工具：`scripts/build_trace_report.py`（仅 Trace）、`scripts/build_html_report.py`（仅 Dashboard）、
`scripts/organize_result_layout.py --refresh`（刷新已组织 run 的摘要）。

## 阶段独立性

Answer 与 Judge 为独立可续跑阶段：检索失败不进 Answer，Answer 失败不进 Judge；失败 case
与成功输出对账后跳过重跑。历史 LongMemEval / LoCoMo / PersonaMem 独立脚本
（`run_reme_retrieval_eval.py` / `run_answer_eval.py` / `run_judge_eval.py` /
`run_reme_end_to_end_eval.py`）仍保留可用。

## 数据集

MemEval-v0.1：298 条冻结 case，覆盖 D01–D08（记忆写入、长期记忆检索、长时跨会话、主动记忆
激活、用户画像、动态更新冲突、超长上下文、隐私与用户隔离），已通过阶段审计。各维度构成、
来源与指标语义见 [`dataset/MemEval-v0.1/README.md`](dataset/MemEval-v0.1/README.md) 及
各维度目录 README。case 用 `scripts/freeze_memeval_selection.py` 冻结，保证消融各 arm 一致。

## Attribution

- Dataset: [LoCoMo](https://github.com/snap-research/locomo) /
  [LongMemEval](https://github.com/xiaowu0162/LongMemEval) /
  [PersonaMem](https://arxiv.org/abs/2504.14234)
- AML pipeline: [Agent Memory Leaderboard](https://github.com/AML-memory/agent-memory-leaderboard)