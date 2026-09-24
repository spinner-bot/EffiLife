# 统一存档纳入 plan-helper 原始快照

**文档性质**：数据管理设计方案（实施前置）
**创建时间**：2026-09-25（Asia/Shanghai）
**适用范围**：`.efl` 存档与 plan-helper registry

## 1. 问题

当前 `.efl` 只保存 time-helper 的日计划和待办，plan-helper 的事件计划仍留在独立服务内。这样导出后无法完整迁移三模块数据，尤其会遗漏软删除槽位、嵌套 group 和 log 引用。

## 2. 方案

- plan-helper 新增数据 API，直接导出 `Plan.plan` 原始字典数组。
- 存档字段使用 `planHelper`，包含：
  - `available`：导出时 plan-helper 服务是否可达；
  - `plans`：原始 plan 快照数组。
- 导入时将快照通过 plan-helper 数据 API 恢复到 registry，而不是调用摘要或 full view 再反向拼装。
- 导入默认使用 replace 语义，使存档成为完整恢复点；重复 ID 和坏结构由 plan-helper API 返回错误，不静默覆盖。

## 3. 保真不变量

- `head`、`main`、`log` 原样保留。
- `main[].plan` 中的空槽位和 `is_active=false` 槽位不删除、不压缩。
- `main[].group` 的字符串键（包括嵌套区间）原样保留。
- 日志中的任务引用不在导出或导入过程中重写。

## 4. 降级行为

- plan-helper 不可用时仍可导出其它数据，但存档明确写入 `available=false`，不伪装成完整三模块备份。
- 导入时若计划服务不可用，已导入的本地数据仍保留，并向用户返回部分恢复提示。

## 5. 验收条件

- 原始快照经过 API 导出—导入后，关键结构深度相等。
- 服务不可用状态可识别。
- 全项目测试、服务级 API 测试和前端构建通过。
