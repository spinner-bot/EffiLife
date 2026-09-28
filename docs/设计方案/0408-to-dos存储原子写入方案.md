# 0408｜to-dos 存储原子写入方案

## 背景

统一 DataManager 已对共享引用和备份采用原子 JSON 写入，但 Python to-dos 的待办、分类和归档仍直接覆盖文件。待办是统一工作区的核心数据，必须具备同等的异常恢复边界。

## 设计决策

- `todos.json`、`categories.json` 和按月归档的 `todos.json` 统一先写同目录临时文件，再用 `os.replace` 替换。
- 临时文件写入后执行 `flush` 和 `fsync`，异常时清理临时文件。
- 不改变 to-dos 文件布局、字段、归档语义或 API 行为。

## 验收标准

1. 三类 to-dos JSON 写入都使用同一原子写入工具。
2. 现有 CRUD、归档和重载行为保持兼容。
3. 统一根目录模式与历史目录模式均可工作。
