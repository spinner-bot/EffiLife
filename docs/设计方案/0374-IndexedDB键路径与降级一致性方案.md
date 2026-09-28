# 0374 IndexedDB 键路径与降级一致性方案

## 问题

统一存储 API 使用逻辑 `key/value` 记录，但历史对象存储的 keyPath 包含 `date` 或 `id`。直接写入 `{ key, value }` 会触发 DataError，导致运行时悄悄退回 localStorage；待办 raw 存储在 IndexedDB 不可用时则没有可用回退路径。

## 决策

- 通用 `set()` 根据当前对象存储的 `keyPath` 镜像写入逻辑 key，兼容已有数据库版本；
- `getRawAll/putRaw/deleteRaw` 使用独立 raw localStorage 命名空间作为降级存储；
- 清空操作同时清理通用和 raw 降级数据，避免恢复 IndexedDB 后出现陈旧数据；
- 数组顺序和业务对象结构不变，不对待办、分类或记录做扁平化。

## 边界

本次不强制升级或重建已有 IndexedDB 数据库，优先避免破坏已有用户数据；后续浏览器测试需覆盖数据库不可用和已有旧 schema 两种场景。
