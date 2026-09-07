# System Adapter

本目录是正式 MemEval Case 与被测记忆系统之间的薄层接口。

阶段24只实现 `ReMeSystemAdapter`：它把八个维度的 `Context Event` 按 Session
转换为现有 ReMe Adapter 已支持的输入，并直接复用现有的启动、写入、索引、检索
和清理逻辑，没有重写 ReMe。

当前边界只包含打开 Case、写入、检索和关闭 Case。画像、删除、用户隔离、Trace、
统计及 capability 判定留到阶段25、26；阶段27 Runner 完成前，`MemEval-v0.1`
仍不会被标记为可直接运行。

以后接入其他 Memory System 时，在本目录增加新的实现即可；不需要修改
Dataset Builder，也不需要让 Runner 理解具体系统的私有格式。
