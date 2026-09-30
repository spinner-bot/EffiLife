# 0491 to-dos 完成事件联动契约

## 已完成

- 增加真实 `TodoAPI` + `EffiLifeIntegration` + time-helper 接收端的端到端测试。
- 验证待办完成事件只创建一条关联时间记录。
- 验证记录包含待办引用和完成时长，并回写 `time_spent`。
- 使用临时数据目录和单例清理，不影响其他测试。

## 验证

- `python -m pytest -q tests/test_todo_time_event_integration.py`
- 全量 Python 测试
- 前端生产构建
