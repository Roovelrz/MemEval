# Memory Eval 双语 Benchmark 改进清单

## 1. 数据集拆分

当前只保留两套独立 Benchmark：

### 英文全量基准

- `LongMemEval-EN-Full`
- 直接读取本地 LongMemEval 官方英文原始数据
- 不翻译
- 不修改原始 benchmark 数据
- 通过现有 Dataset Adapter 转换为统一 `EvalCase`
- 支持 `cases` 参数控制测试数量
- `cases = 0` 时运行全部数据
- 用于大样本 Benchmark 和整体 Memory 能力测试

### 中文本地化基准

- `LongMemEval-ZH-20-v0.1`
- 保持现有 20 个 case
- 暂时不扩充
- 不重新翻译
- 不修改现有 case selection
- 保持当前 dataset version 和 hash
- 用于中文 Memory 能力测试

禁止把英文和中文 case 混进同一次 Eval Run。

---

## 2. Dataset Registry

增加统一 Dataset Registry。

当前注册：

```text
LongMemEval-EN-Full
LongMemEval-ZH-20-v0.1
```

预留：

```text
LoCoMo-EN-Full
LoCoMo-ZH-Localized

PersonaMem-EN-Full
PersonaMem-ZH-Localized
```

每个 Dataset 至少记录：

```text
dataset_id
dataset_name
source_dataset
language
version
path
case_count
translated
```

本阶段只实现 LongMemEval。

---

## 3. Runner 调整

Runner 增加数据集选择能力。

主要参数：

```text
--dataset
--cases
--start
--shuffle
--seed
--top-k
--memory-adapter
--output-dir
--run-id
```

英文全量：

```text
dataset = LongMemEval-EN-Full
cases = 0
```

中文：

```text
dataset = LongMemEval-ZH-20-v0.1
cases = 20
```

两套数据必须复用：

```text
Memory Adapter
Retrieval Eval
Answer
Judge
Trace
Root Cause
HTML Reporter
```

禁止为英文数据单独开发另一套 Eval 流程。

---

## 4. Run 信息补充

每次运行的 `run_config.json` 和 `trace_summary.json` 增加：

```text
dataset_id
dataset_name
dataset_version
source_dataset
language
translated
case_count
```

保证 HTML Reporter 能识别当前结果来自英文还是中文数据。

---

## 5. 结果目录

统一按语言数据集分开保存：

```text
results/
├── en_full/
│   └── <memory_backend>/
│       └── <run_id>/
│
└── zh_localized/
    └── <memory_backend>/
        └── <run_id>/
```

例如：

```text
results/
├── en_full/
│   └── reme/
│       └── reme-longmemeval-en-full/
│
└── zh_localized/
    └── reme/
        └── reme-longmemeval-zh20/
```

---

## 6. Dashboard 增加双 Benchmark 展示

首页新增一级模块：

```text
Benchmark 表现
```

只展示两套结果：

| Benchmark | Cases | Recall@10 | MRR | Answer Accuracy | Grounded E2E |
|---|---:|---:|---:|---:|---:|
| 英文全量基准 | N | ... | ... | ... | ... |
| 中文本地化基准 | 20 | ... | ... | ... | ... |

使用原始字段：

```text
case_count
hit_at_10
recall_at_10
mrr
answer_accuracy
grounded_end_to_end_accuracy
pipeline_success_rate
```

---

## 7. Dashboard 增加 Benchmark 切换

Dashboard 顶部增加：

```text
Benchmark
```

当前两个选项：

```text
英文全量基准
中文本地化基准
```

切换后，下方全部页面同步切换到对应 Run 数据：

```text
综合能力评分
工程健康度
检索质量
回答质量
能力维度表现
四象限分析
失败归因
流程观测
性能与时延
API 稳定性
Case 追踪
```

---

## 8. 预留后续 Benchmark

Dashboard 的 Benchmark 切换机制必须支持后续直接增加：

```text
LoCoMo 英文全量
LoCoMo 中文本地化
PersonaMem 英文全量
PersonaMem 中文本地化
```

新增 Benchmark 时只允许：

```text
增加 Dataset Adapter
注册 Dataset
增加对应 Run
```

不得重新开发 Dashboard 页面。

---

## 9. 英文全量 Benchmark 展示重点

英文全量主要查看：

```text
case_count
hit_at_10
recall_at_10
mrr
answer_accuracy
grounded_end_to_end_accuracy
question_type_breakdown
root_cause_distribution
latency_breakdown
api_stability
```

用途：

- 大样本整体能力
- Memory Backend 横向测试
- 版本回归
- 稳定性测试

---

## 10. 中文本地化 Benchmark 展示重点

中文 20 case 主要查看：

```text
hit_at_10
recall_at_10
mrr
answer_accuracy
grounded_end_to_end_accuracy
question_type_breakdown
root_cause_distribution
cases
```

用途：

- 中文实际能力
- 中文 Bad Case
- 中文 Retrieval 问题
- 中文 Answer 问题
- 开发侧中文回归测试

---

## 11. 四象限图同时支持两套 Benchmark

现有：

```text
端到端能力四象限分析
```

根据当前 Dashboard 选择的 Benchmark 加载对应 Case。

英文模式：

```text
LongMemEval-EN-Full Cases
```

中文模式：

```text
LongMemEval-ZH-20-v0.1 Cases
```

点击任意 Case 点继续跳转：

```text
cases/<case_id>.html
```

不改变现有 `quadrant` 和 Trace 逻辑。

---

## 12. 本阶段开发顺序

- [x] 接入本地 LongMemEval 英文原版
- [x] 注册 `LongMemEval-EN-Full`
- [x] 保留 `LongMemEval-ZH-20-v0.1`
- [x] 英文数据通过现有 Dataset Adapter 进入统一 `EvalCase`
- [x] 英文跑通 1 case
- [x] 英文跑通 20 case
- [ ] 英文跑通全量
- [x] Run 信息增加 dataset 和 language 字段
- [x] Results 按英文和中文分别保存
- [x] Dashboard 增加 Benchmark 表现模块
- [x] Dashboard 增加英文全量和中文本地化切换
- [x] Dashboard 所有指标随 Benchmark 切换
- [x] 四象限随 Benchmark 切换
- [x] Case Trace 随 Benchmark 切换
- [x] 预留 LoCoMo 和 PersonaMem 后续接入位置

> 当前英文全量 500 case 已完成只读加载与统一 Adapter 验收，但尚未发起完整
> Answer/Judge Run。英文 20 case 的串行实测总耗时约 4 分钟、LLM cost 约
> 0.033 USD；当前端到端 Runner 已默认使用 Retrieval 2、Answer 4、Judge 4
> workers。本地 4-case Retrieval 并发 2 已实测通过；据现有小样本推算，本地
> 全量约需 55–70 分钟，成本仍约 0.82 USD。该时间是估算值，正式启动前应先用
> 20 case 复测；服务器可从 Retrieval 4 开始逐档提高。

---

## 13. 当前明确不做

- [ ] 不扩充中文 20 case
- [ ] 不翻译剩余 LongMemEval 数据
- [ ] 不做英文 Paired 20
- [ ] 不做 Language Gap
- [ ] 不做 Recall Gap
- [ ] 不做 Accuracy Gap
- [ ] 不做 Dataset 筛选器
- [ ] 不改 Comparison Analyzer
- [ ] 不增加新的 Comparison Schema
- [ ] 不修改现有 Trace Schema
- [ ] 不修改 Root Cause 逻辑
- [ ] 不重新开发 HTML Reporter
- [ ] 不在本阶段接 LoCoMo
- [ ] 不在本阶段接 PersonaMem

---

## 14. 最终验收

- [ ] 能直接读取 LongMemEval 官方英文全量数据
- [ ] 英文无需翻译即可进入现有 Eval Harness
- [ ] 英文和中文分别独立运行
- [ ] 中文现有 20 case 完全不受影响
- [ ] 两套数据使用同一套 Memory Adapter
- [ ] 两套数据使用同一套 Retrieval、Answer、Judge 和 Trace
- [ ] Dashboard 首页同时展示两套 Benchmark 结果
- [ ] Dashboard 可以切换英文全量和中文本地化
- [ ] 切换后能力维度、四象限、失败归因和 Case Trace 同步变化
- [ ] 后续 LoCoMo、PersonaMem 可以复用同样的切换机制
- [ ] Reporter 不修改任何原始 Eval 产物

## 最终结构

```text
Memory Eval
│
├── LongMemEval 英文全量基准
│   └── 大样本整体 Benchmark
│
└── LongMemEval 中文本地化基准
    └── 20 Case 中文能力 Benchmark
```

当前 Dashboard 只需要回答两个问题：

```text
英文全量基准
这个 Memory 在大样本标准 Benchmark 上表现怎么样

中文本地化基准
这个 Memory 面向中文场景表现怎么样
```
