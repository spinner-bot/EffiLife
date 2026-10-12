# Python 统一存档数据形状校验方案

- 状态：[已实现并验证]
- 创建时间：2026-09-29
- 执行者：Codex
- 关联目标：让 Python 迁移工具与统一前端对 `.efl` 存档采用一致的基础校验边界

## 1. 问题

Python `read_workspace_bundle()` 当前只确认 canonical 数据集是否齐全，不检查数据集顶层类型。一个 `records` 为数组、`todos` 为对象或 `plan_helper` 为字符串的存档可能通过 Python 校验，但会在前端导入时失败或产生不同结果。

## 2. 方案

在 `read_workspace_bundle()` 完成完整性校验后，增加 canonical 数据集基础形状校验：

- `app`：对象；
- `records`：对象，且每个日期桶为数组；
- `todos`：数组；
- `todo_categories`：数组；
- `plan_helper`：对象，若存在 `plans` 则必须为数组。

该层只校验跨运行时稳定的容器形状，不复制前端领域字段归一化逻辑；具体字段迁移仍由适配器负责。

## 3. 约束

- 不改变通用 `read_bundle()` 对非工作区 bundle 的宽松行为。
- 不要求 Python 侧理解前端所有可选字段。
- 错误应在写入或迁移前抛出，避免产生半导入状态。

## 4. 验收

- 合法 canonical workspace bundle 继续通过读取和验证。
- 任一核心数据集顶层类型错误时，Python 侧拒绝读取并给出数据集名称。
- records 日期桶类型错误时，错误信息包含具体日期。
