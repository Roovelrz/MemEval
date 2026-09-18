# Memory Dataset 构建与 Eval 框架搭建

## 一、数据集思路

8 个维度完整跑通"数据构建 → 系统运行 → 指标计算"闭环。

- **context_ref 复用**：Context 与 Case 分离，多 Question 共用同一 Context 只存引用，避免超长数据重复。
- **完整性核验**：case_id/query_id 全局唯一、Evidence 可解析、无答案泄漏进 Context、Source Audit 7/7、最终 PASS。

## 二、各维度侧重点

| 维度 | 侧重点 |
| --- | --- |
| D01 记忆抽取与写入 | LongMemEval Evidence ≠ 应写入 Memory，需人工 Gold Memory 标注（有限 Scoring Window）算 Write P/R |
| D02 基础长期记忆 | 纯检索切片，排除拒答变体，Context 移除 has_answer 防泄漏；Hit@K/Recall@K/MRR |
| D03 长时间跨度对话 | LoCoMo 原生 Temporal + 受控生命周期（deleted_at/expected_active）测 Deleted Hit |
| D04 主动记忆激活 | 必须 Positive/Negative 成对，否则识别不出无条件调用 Memory |
| D05 检索召回 | 纯检索召回 |
| D06 动态更新与冲突 | 8 个 Context 展开 37 Case，重建冲突链，校验 questions/answers 严格对应 |
| D07 超大规模长上下文 | Recall Degradation 必须来自同 Context 的 Paired Scale Case，不伪造 Evidence |
| D08 隐私与用户隔离 | 跨用户隔离/删除/Canary 泄漏检测，用人工唯一 Token 代替真实敏感数据 |

## 三、Eval 框架：Adapter 层

`Dataset → Memory → Answer LLM → Judge LLM → Trace` 四类 Adapter，Runner 只组织流程不碰私有格式
（`memory_eval/adapters/`，入口 `scripts/run_memeval.py`）：

| 层 | 作用 | 当前实现 |
| --- | --- | --- |
| dataset | 读 benchmark → 统一 case | longmemeval / locomo / personamem-v2 |
| memory | 隔离/写入/检索/清理 | reme / off（无记忆对照） |
| llm | 请求/重试/usage | openai-compatible（Answer/Judge） |
| Trace | 汇总 → 报告/Dashboard | memeval（与八维绑定） |

- 统一 case 结构：`case_id/question/gold_answer/sessions[]/evidence_session_ids`。
- `systems/` 再包一层 System Adapter 声明能力边界，不支持的能力返回 `unsupported` 不记 0。
- 新增实现 = 新增文件 + registry 登记，Runner 不加专用分支；API 密钥只在 `.env`。

## 四、Eval 框架：Result / Dashboard 聚合层

- 链路：`scripts/run_memeval.py` 编排 Retrieval → Answer → Judge → Trace → Dashboard；上游成功才进
  下游，失败 case 按 case_id 续跑。
- 结果按 `results/memeval_v0_1/<system>/<run-id>/` 隔离（reme / off 各自成目录）。
- **指标口径**：D02 保持 session 级 Hit@K/Recall@K/MRR（primary K=3）+ answer_accuracy；D05 为
  needle 级纯检索召回（K=1/3/5/10 全档位），Answer/Judge 记 NOT_APPLICABLE。
- **Dashboard**：静态 HTML，8 维展示不变、不支持能力标"不支持"；已移除跨维度 CORE METRICS 段防误读。
- 展示升级后旧 run 用 `--trace-only` 从持久化产物重建报告、不重跑。
- 基线：`dashboard-baseline-v1`（commit 34d305d）。