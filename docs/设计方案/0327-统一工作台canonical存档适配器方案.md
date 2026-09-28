# 0327-统一工作台 canonical 存档适配器方案

## 背景

前端 `.efl` 与公共 Python 交换层已经使用相同的 `effilife.bundle` ZIP 外壳，但 Python 层原先只提供任意数据集接口。迁移工具可能因此自行命名数据集，逐渐偏离统一工作台协议。

## 方案

固定五个 canonical 数据集：

`app`、`records`、`todos`、`todo_categories`、`plan_helper`。

公共层新增 `export_workspace_bundle()` 与 `read_workspace_bundle()`，分别负责按统一名称写出和校验完整工作台包；底层通用 `export_bundle()` / `read_bundle()` 继续保留，用于兼容其他迁移场景。

## 兼容性

不改变现有 ZIP 格式、manifest 字段或前端导入逻辑，只增加 Python 侧的明确适配入口。
