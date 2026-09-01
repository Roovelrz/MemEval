# Adapter 层

这里是 Eval Harness 与外部实验对象之间的唯一边界。Runner 只负责组织
`Dataset -> Memory -> Answer LLM -> Judge LLM -> Trace`，不再直接理解某个数据集、
Memory 实现或模型服务的私有格式。

## 三类 Adapter

- `dataset/`：读取原始 benchmark，并转换成统一 case。当前包含
  `longmemeval`、`locomo`、`personamem-v2`；`auto` 可根据文件结构自动识别。
- `memory/`：完成单 case 隔离、写入、索引、检索和清理。当前包含真实
  `reme` 与无记忆对照 `off`。
- `llm/`：完成模型请求、错误归类、重试和 usage 透传。当前
  `openai-compatible` 同时供 Answer 与 Judge 使用，可通过不同环境变量连接不同端点。

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

日常运行只编辑仓库根目录的 `run_eval.py`：

- `dataset`：数据文件绝对路径；
- `dataset_adapter`：`auto` 或具体数据集 Adapter 名；
- `memory_adapter`：`reme` / `off`；
- `answer_llm_adapter`、`judge_llm_adapter`：LLM Adapter 名。

API 密钥和服务地址不写入代码。DeepSeek 等配置继续放在被 Git 忽略的 `.env`；
公司的本地模型配置 `local_LLM.txt` 也只用于本地，不应进入 Git。
