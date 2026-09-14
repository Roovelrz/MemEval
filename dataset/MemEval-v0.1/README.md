# MemEval v0.1 数据集

这是经过人工审核与全局完整性核验的 Agent Memory Evaluation 数据集版本。

## 数据规模

- 维度：8 个
- Case：298 条
- 全局重复 `case_id`：0
- 全局重复 `query_id`：0
- 缺失 Context 引用：0
- Source Audit：7/7 通过
- 最终完整性核验：PASS

各维度 Case 数量：

| 维度 | Case 数量 |
|---|---:|
| D01 记忆抽取与写入 | 37 |
| D02 长期记忆检索 | 37 |
| D03 长时间跨度对话 | 38 |
| D04 主动记忆激活 | 38 |
| D05 用户画像与偏好 | 37 |
| D06 动态更新与冲突 | 37 |
| D07 超长上下文 | 37 |
| D08 隐私与用户隔离 | 37 |

## 目录说明

- `dimensions/`：D01-D08 的正式 Case、Context、Manifest 和维度说明。
- `manifests/`：上游数据版本锁定信息及最终核验报告。
- `quality/`：跨维度覆盖矩阵。
- `Agent Memory Eval 数据集构建开发文档 v0.1.md`：数据集构建规范。

`raw/` 是上游数据集的下载缓存，不属于本版本的正式发布内容，因此未重复提交。来源、固定 revision、所需文件和哈希记录在 `manifests/` 中。

## 评测入口

本数据集是 `memory_eval_pipeline` 的默认评测对象：

```powershell
python scripts/run_memeval.py --run-id reme-full          # ReMe 完整系统
python scripts/run_memeval.py --memory-adapter off        # 无记忆消融对照
```

各维度的具体指标口径见 `dimensions/*/v0.1/README.md` 的"评测口径"一节；
运行方法与结果布局见仓库根目录 `USAGE_ZH.md`。case 选择已冻结，
消融实验各 arm 天然一致。

## Git LFS

D07/D08 等维度包含超长 JSONL Context，本目录下的 `*.jsonl` 使用 Git LFS 管理。克隆仓库后请安装 Git LFS，并执行：

```powershell
git lfs pull
```

## 核验方式

阶段 23 使用 `dataset/build_pipeline/audit.py` 直接核验正式目录。核验结果仅在运行时返回，不保留中间报告文件；当前版本核验结果为 PASS。
