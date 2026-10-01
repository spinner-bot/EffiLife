"""
事件处理器注册中心

一键注册所有跨模块联动处理器。
"""

from typing import Optional
from ..event_bus import EventBus
from ..api_gateway import APIGateway
from ..data_manager import DataManager

from .plan_todo import PlanTodoLinker
from .todo_time import TodoTimeLinker
from .stats_correlation import StatsCorrelator


def register_all_handlers(
    gateway: Optional[APIGateway] = None,
    data_manager: Optional[DataManager] = None,
    event_bus: Optional[EventBus] = None,
    enable_plan_todo_automation: bool = False,
) -> dict:
    """
    注册所有跨模块事件处理器

    Returns:
        包含所有联动器实例的字典
    """
    gw = gateway or APIGateway.get_instance()
    dm = data_manager or DataManager.get_instance()
    eb = event_bus or EventBus.get_instance()

    # PH 与 TD 默认保持独立。旧的自动生成/完成联动仅在调用方明确
    # opt-in 时注册，避免统一应用启动后隐式改变 TD 数据。
    plan_todo = PlanTodoLinker(gw, dm) if enable_plan_todo_automation else None
    todo_time = TodoTimeLinker(gw, dm)
    stats = StatsCorrelator(gw, dm)

    # 注册事件处理器
    if plan_todo is not None:
        plan_todo.register()
    todo_time.register()

    return {
        'plan_todo_linker': plan_todo,
        'todo_time_linker': todo_time,
        'stats_correlator': stats,
    }
