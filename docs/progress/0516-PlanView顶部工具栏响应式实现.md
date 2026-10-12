# 1022 PlanView 顶部工具栏响应式实现

## 日期

2026-10-02

## 背景与目标

落实 1021 设计记录，修复 TH PlanView 顶部返回、Tab 和新增按钮在窄桌面/平板窗口中的横向挤压风险。

## 实施内容

- 顶部工具栏允许 flex 换行，并让 Tab 容器可以收缩。
- 移动断点下将 Tab 放到第二行并占满可用宽度。
- 新增按钮保持在第一行右侧，不改变已有导航和操作语义。

## 兼容性与边界

只调整 PlanView CSS 布局，继续使用现有主题变量和移动断点；TH 数据、PH/TD 边界、路由和主题持久化不变。

## 验证

- `python -m pytest tests/test_desktop_workspace_layout.py -q`：20 passed。
- `python -m pytest -q`：782 passed。
- 前端 `npm run build`：当前环境未提供 Node/npm，待 CI 执行。

## 提交与推送

实现验证通过后与本次代码变更一起提交并推送；保留用户保护项不暂存。
