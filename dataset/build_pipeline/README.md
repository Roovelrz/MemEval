# 数据集构建侧 Adapter

本目录只服务于 **MemEval 数据集构建**，与 `memory_eval/adapters/` 下的评测运行 Adapter 分开：

- `sources/`：读取七套上游原始数据，保留来源 ID、原始 Gold 和来源元数据，并统一为 Canonical Event。
- `staging.py`：按阶段 20 约定写出 `records.jsonl + contexts/`，并拒绝向非空目录混写。
- `dimensions/`：阶段 21 的八个维度 Builder，负责抽样、配对、Gold 派生和维度校验。
- `dataset/MemEval-v0.1/`：已经冻结的正式数据，不由本目录的测试改写。

## 当前完成范围

阶段 17 的七个 Source Adapter 已建立：

| Adapter | 输入 | 当前处理 |
| --- | --- | --- |
| LongMemEval | JSON / JSONL | 复用现有解析器，转为 Canonical Event |
| LoCoMo | JSON | 复用现有 Session、Timestamp、Evidence 映射 |
| PrefEval | 三个白名单 Parquet | 显式偏好、隐式选择、隐式画像统一读取 |
| PersonaMem-v2 | text/32K CSV | 复用现有画像与 32K 历史索引 |
| MemoryAgentBench | Conflict Resolution Parquet | 保留一个 Context 对多个 Question/Answer |
| BEAM | 100K、500K、1M、10M Parquet | 统一嵌套 Chat，保留 Scale 和 probing questions |
| AgentMemBench | MemDialogue-v2 JSONL | 保留 memory event、query、ground truth 和来源字段 |

LongMemEval、LoCoMo、PersonaMem-v2 采用 Wrapper，现有 Eval 侧 Adapter 没有被改写。

阶段 20、21 也已完成代码化：

| Builder | 来源 | 核心逻辑 | 默认目标数 |
| --- | --- | --- | ---: |
| D01 | LongMemEval | Evidence 转写入候选，生成待审核原子记忆 | 37 |
| D02 | LongMemEval | 问答与 Evidence 检索 Gold | 37 |
| D03 | LoCoMo | 时间戳、间隔与生命周期 | 38 |
| D04 | PrefEval | 显式负例与隐式正例成对、正负平衡 | 38 |
| D05 | PersonaMem-v2 | 画像条目与 Evidence | 37 |
| D06 | MemoryAgentBench | 一个 Context 展开多个 Query，保留冲突 Gold | 37 |
| D07 | BEAM | 展开 probing questions，关联 Scale 与 Evidence | 37 |
| D08 | AgentMemBench | 19 个跨用户、10 个删除、8 个 Canary 场景 | 37 |

其中 D01、D05、D06 如果在**以后新增原始样本**时没有传入已审核语义标注，会明确写入 `semantic_review_required`；D07 新样本无法从上游 probe 解析 Evidence 时会写入 `evidence_review_required`。这些标记只描述新生成的 Staging 草稿，不代表已经冻结的 `MemEval-v0.1` 仍待审核。

正式 v0.1 通过 `ReviewedBenchmark` 读取原有人工结论。当前逐 Case 状态为：D01 37 条通过、D04 38 条通过、D05 37 条修复后通过、D06 33 条直接通过且 4 条替换后通过、D07 37 条通过，不会重新降级为待审核草稿。

## Canonical Source Record

每条输出包含：

```text
source_dataset
source_record_id
events[]
source_gold
source_metadata
```

每个 Event 保留：

```text
event_id
session_id
sequence
role
content
timestamp
source_id
metadata
```

这里的 `source_gold` 是上游提供的候选答案或标注，不等于最终维度 Gold。最终 Case 数量、配对、抽样和 Gold Payload 由 Dimension Builder 决定。

## 最小用法

Parquet 数据源先安装独立依赖：

```powershell
python -m pip install -r dataset/build_pipeline/requirements.txt
```

然后创建 Adapter 并流式读取：

```python
from pathlib import Path

from dataset.build_pipeline.sources import create_source_adapter

adapter = create_source_adapter("locomo")
records = adapter.iter_records(Path(r"E:\LRZ_Workplace\fork\datasets\raw\locomo\data\locomo10.json"))
first_record = next(records)
```

完整核查：

```python
report = adapter.audit(source_path)
assert report.ok, report.errors
```

大文件可先用 `adapter.audit(source_path, limit=10)` 做小样本接口检查；正式产出前仍需无 `limit` 的全量核查。

阶段 20 Staging 写出：

```python
from dataset.build_pipeline import write_staging_records

write_staging_records(adapter.iter_records(source_path), staging_output_dir)
```

## Dimension Builder 边界

`dimensions/base.py` 已提供文档约定的六步接口：

```text
load_candidates()
filter_candidates()
derive_gold()
sample_cases()
validate_cases()
build()
```

`d01_write.py` 到 `d08_privacy.py` 已实现并注册：

```python
from dataset.build_pipeline import create_dimension_builder

builder = create_dimension_builder("D03")
result = builder.build(canonical_source_records)
```

阶段 21 输出是可审计的 Staging Case。现有 `dataset/MemEval-v0.1` 是已经人工审核、冻结并采用 `envelope + gold` 的正式版本，本构建代码不会覆盖它。

阶段 22 如需生成开发文档约定的统一 `cases.jsonl + contexts/` 交付布局，可显式导出到一个空目录：

```python
from dataset.build_pipeline import export_benchmark_layout

export_benchmark_layout("dataset/MemEval-v0.1", output_directory)
```

阶段 23 的完整核查直接在内存中返回报告，不保存中间验证文件：

```python
from dataset.build_pipeline import audit_benchmark

report = audit_benchmark("dataset/MemEval-v0.1")
report.raise_for_errors()
```

该核查覆盖 298 条 Case、人工审核状态、全局 Case/Query 唯一性、Context 与 Evidence 引用、553 个正式文件哈希，以及 D04 配对、D07 四档规模一致性和 D08 隔离/删除/Canary 规则。开发文档中的 300 条是去重前目标；当前冻结版按用户确认删除两条跨维度重叠 Case 后为 298 条。
