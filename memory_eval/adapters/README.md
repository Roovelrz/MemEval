# Adapter 层

这里是 Eval Harness 与外部实验对象之间的唯一边界。Runner 只负责组织
`Dataset -> Memory -> Answer LLM -> Judge LLM -> Trace`，不再直接理解某个数据集、
Memory 实现或模型服务的私有格式。

## 四类 Adapter

- `dataset/`：读取原始 benchmark，并转换成统一 case。当前包含
  `longmemeval`、`locomo`、`personamem-v2`；`auto` 可根据文件结构自动识别。
  MemEval-v0.1 复合 benchmark 由三个来源数据集按维度重新组装并冻结，见
  `dataset/MemEval-v0.1/README.md`。
- `memory/`：完成单 case 隔离、写入、索引、检索和清理。当前包含真实
  `reme` 与无记忆对照 `off`。
- `llm/`：完成模型请求、错误归类、重试和 usage 透传。当前
  `openai-compatible` 同时供 Answer 与 Judge 使用，可通过不同环境变量连接
  不同端点（含 vLLM 等本地 OpenAI 兼容服务）。
- `Trace/`：把各阶段产物转换成 Trace 报告与 Dashboard 的输入。当前只有
  `memeval`，与 MemEval 八维结构绑定。

## 可替换性约定

前三类是实验变量，Trace 是评测框架自身的配套产物：

| 层 | 角色 | 替换方式 |
| --- | --- | --- |
| dataset | 实验变量 | 新增实现文件 + `registry.py` 登记 |
| memory | 实验变量 | 新增实现文件 + `registry.py` 登记 |
| llm | 实验变量 | 新增实现文件 + `registry.py` 登记 |
| Trace | 框架配套 | 随评测框架演进，不作为实验变量 |

memory 层之上还有一层 `memory_eval/systems/` 的 System Adapter（协议封装，
声明能力边界并包住 Memory Adapter），见
[`memory_eval/systems/README.md`](../systems/README.md)。

每类目录中的 `base.py` 定义稳定输入输出，`registry.py` 负责按名称创建实现。
增加新实现时，只新增实现文件并在对应 registry 登记；Runner 不应加入该实现的
专用分支。

## 统一 case 结构

Dataset Adapter 至少输出：

- `case_id`、`question`、`gold_answer`、`question_type`、`question_date`
- `sessions[]`，每个 session 含 `session_id`、`timestamp`、`messages[]`
- `evidence_session_ids[]`

这样同一个 Memory Adapter 可以无差别地消费不同 benchmark，Answer、Judge 和
Trace 也不需要知道原始数据来自 JSON、JSONL、CSV 或外部历史文件。

## 配置入口

日常运行通过 `scripts/run_memeval.py` 的命令行参数选择实现：

- `--data`：数据目录（默认使用内置冻结的 MemEval-v0.1）；
- `--memory-adapter`：`reme` / `off`；
- LLM 端点通过 `DEEPSEEK_*` 环境变量或 `.env` 配置（见根目录 USAGE_ZH.md）。

API 密钥和服务地址不写入代码。DeepSeek 等配置继续放在被 Git 忽略的 `.env`；
公司的本地模型配置也只用于本地，不应进入 Git。
