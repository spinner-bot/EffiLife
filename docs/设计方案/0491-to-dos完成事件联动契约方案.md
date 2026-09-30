# 0491 to-dos 完成事件联动契约方案

## 背景

EffiLife 的 Python 集成层通过共享 `EventBus` 协调 to-dos 与 time-helper。`TodoTimeLinker` 已实现“完成待办后自动创建时间记录并累计已用时”，但原有测试主要验证事件发布或静态引用，没有验证三个运行组件实际连通。

## 方案

增加端到端契约测试：创建 `EffiLifeIntegration`，注册真实 `TodoAPI` 和一个记录调用的 time-helper 接收端，完成一个带时长的待办，验证时间记录日期、关联待办 ID、内容和时长，并验证待办的 `time_spent` 被累计。

测试使用临时数据目录和集成单例重置，不改变生产行为，也不把 PH/TD 业务实体强行合并。

## 验收

- 共享事件总线确实触发 `TodoTimeLinker`。
- 自动生成的时间记录带有 `related_todo_id`，时长与完成事件一致。
- 待办累计用时只增加一次。
- 测试结束后清理集成单例，避免污染其他测试。
