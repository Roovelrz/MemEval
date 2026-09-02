# D03 v0.1

本目录按照开发文档第 11 节构建 D03 的 38 条长时间跨度对话样本。

- `contexts/`：保存由 LoCoMo 官方 `locomo10.json` 映射得到的规范化事件；原生问题共享会话上下文，生命周期样本使用带派生删除事件的独立上下文。
- `cases/`：保存公共信封和 `temporal` Gold Payload。
- 样本组成：24 条原生 Temporal、8 条跨会话 long-gap、6 条派生 lifecycle。
- 官方 category `2` 映射为 Temporal，category `1` 映射为 multi-hop；不按论文枚举顺序猜测类别。
- 原生问题、答案和证据 `dia_id` 均保持不变；依赖真实图像、空答案或证据不可解析的样本不进入本切片。
- `time_gap_days` 表示最早 Gold 证据到查询时刻之间的最大整日间隔；源时间戳没有时区，因此规范化值不附加伪造时区。
- 生命周期样本在最后一次原生会话后 1 天追加 `control/forget` 事件，再于 1 天后发起原问题；`expected_active=false` 表示原记忆不得被命中。
- `gold_answer` 在生命周期样本中仅用于标识被删除事实并保留来源追踪；该子集按 Deleted Hit Rate 评估，不作为删除后的应答目标。
