# 1024 PlanView 今日计划选择器响应式实现

## 日期

2026-10-02

## 背景与目标

落实 1023 设计，消除 PlanView 今日计划卡在移动宽度下的控件挤压风险。

## 实施内容

- 移动断点下允许计划卡标题和工具组换行。
- 计划标签独占一行，下拉框可伸缩，新建按钮保持独立操作区域。

## 兼容性与边界

仅调整 PlanView 的移动布局，不改变计划数据、操作逻辑、路由、主题和模块边界。

## 验证

- `python -m pytest tests/test_desktop_workspace_layout.py -q`：21 passed。
- `python -m pytest -q`：783 passed。
- `npm run build`：当前环境未提供 Node/npm，待 CI 执行。

## 提交与推送

本报告与实现一起提交并推送；用户保护项未暂存。
