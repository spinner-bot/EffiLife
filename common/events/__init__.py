"""
事件处理器 - 跨模块自动化

注册事件处理器，实现模块间的联动功能：
- plan-helper 创建计划时自动生成 to-dos
- to-dos 完成任务后自动记录到 time-helper
- time-helper 统计时关联计划和待办
"""

from .plan_todo import PlanTodoLinker
from .todo_time import TodoTimeLinker
from .stats_correlation import StatsCorrelator
from .registry import register_all_handlers

__all__ = [
    'PlanTodoLinker', 'TodoTimeLinker', 'StatsCorrelator',
    'register_all_handlers',
]
