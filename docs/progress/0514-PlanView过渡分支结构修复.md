# 1020 PlanView 过渡分支结构修复

## 问题

PlanView 的工作台内容使用 Vue `<Transition>` 在概览和管理视图之间切换。两个条件根节点之间存在模板注释节点，开发编译器可能将其视为额外子节点，触发“Transition expects exactly one child”的警告，并导致开发遮罩层出现。

## 修复

- 将说明注释放到 `<Transition>` 外部。
- 保证 `manageView` 的 `v-if` 与 `v-else` 根节点在过渡组件内部直接相邻。
- 增加源代码契约，防止后续在两个分支之间插入节点。

## 边界

本次只修复 TH 工作台的视图过渡结构，不改变计划数据、PH/TD 边界、主题配置或路由。

## 验证

- `python -m pytest tests/test_plan_transition_contract.py -q`
- `python -m pytest -q`
- 前端生产构建待具备 Node/npm 的 CI 环境执行。
