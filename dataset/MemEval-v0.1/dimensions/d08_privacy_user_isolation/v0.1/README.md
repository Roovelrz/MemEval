# D08 v0.1

本目录按照开发文档第16节构建 AgentMemBench 隐私与用户隔离评测集。

- 共37个 Case：19个跨用户隔离、10个删除、8个禁止 Canary 暴露。
- 所有公开来源均固定到 AgentMemBench MemDialogue v2 revision `186c9a54edd47aae42d8b6990520f8e902b60303`。
- 只使用官方 release-verified 的 `memdialogue_v2.jsonl`、meta 和 deterministic audit；没有重新抓取或构建 WildChat。
- 原始发布不包含 WildChat 对话 turn，因此 Context 中的来源内容明确标记为上游抽取的 `raw_text`；未伪造原始角色、时间或 turn-level Evidence。
- 19个跨用户 Case 在同一 Tenant 内组合两个不同用户，只允许查询者自己的 Memory。
- 10个删除 Case 明确记录 ingest、删除前验证、delete、删除后查询四步协议。
- 8个 Canary Case 使用人工生成且无现实意义的全局唯一 Token，并跨 Tenant 隔离。
- 所有 `owner_user_id` 与 `querying_user_id` 均不同；所有允许、禁止、删除 Memory ID 均由构造规则确定。
- D08 标签不依赖开放式语义推断，来源事件已由官方 release verifier 通过，因此无需额外人工审核。
- 当前状态为 `complete`。

目录说明：

- `cases/`：37个隐私评测 Case。
- `contexts/`：37个按 Case 隔离的 JSONL Context，以及 `index.json`。
- `manifest.json`：来源、抽样、场景配额、自动核验、限制和全部文件哈希。
