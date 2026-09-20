"""
to-dos 事件发射器

在 to-dos 操作时自动发布事件到事件总线，
实现与 plan-helper、time-helper 的联动。

集成方式：在 TodoAPI 的关键方法中调用 emit 函数。
"""

import sys
from pathlib import Path

# 尝试导入 common（集成层可能不在路径中）
try:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from common.event_bus import EventBus, EventType
    HAS_INTEGRATION = True
except ImportError:
    HAS_INTEGRATION = False


def emit_todo_created(todo_data: dict):
    """发射待办创建事件"""
    if not HAS_INTEGRATION:
        return
    try:
        eb = EventBus.get_instance()
        eb.emit(
            event_type=EventType.TODO_CREATED.value,
            source_module='to-dos',
            data={
                'todo_id': todo_data.get('id', ''),
                'title': todo_data.get('title', ''),
                'related_plan_id': todo_data.get('related_plan_id'),
                'priority': todo_data.get('priority', 'normal'),
                'category': todo_data.get('category', 'default'),
            },
        )
    except Exception:
        pass


def emit_todo_completed(todo_data: dict, time_spent=None):
    """发射待办完成事件"""
    if not HAS_INTEGRATION:
        return
    try:
        eb = EventBus.get_instance()
        eb.emit(
            event_type=EventType.TODO_COMPLETED.value,
            source_module='to-dos',
            data={
                'todo_id': todo_data.get('id', ''),
                'title': todo_data.get('title', ''),
                'time_spent': time_spent or todo_data.get('time_spent'),
                'related_plan_id': todo_data.get('related_plan_id'),
            },
        )
    except Exception:
        pass


def emit_todo_cancelled(todo_data: dict):
    """发射待办取消事件"""
    if not HAS_INTEGRATION:
        return
    try:
        eb = EventBus.get_instance()
        eb.emit(
            event_type=EventType.TODO_CANCELLED.value,
            source_module='to-dos',
            data={
                'todo_id': todo_data.get('id', ''),
                'title': todo_data.get('title', ''),
            },
        )
    except Exception:
        pass


def emit_todo_updated(todo_data: dict, changes: dict):
    """发射待办更新事件"""
    if not HAS_INTEGRATION:
        return
    try:
        eb = EventBus.get_instance()
        eb.emit(
            event_type=EventType.TODO_UPDATED.value,
            source_module='to-dos',
            data={
                'todo_id': todo_data.get('id', ''),
                'changes': changes,
            },
        )
    except Exception:
        pass
