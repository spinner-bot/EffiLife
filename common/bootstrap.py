"""
EffiLife 集成启动器

初始化所有共享组件，注册模块到 API 网关，启动事件处理器。
"""

import sys
from pathlib import Path

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.event_bus import EventBus, EventType
from common.data_manager import DataManager
from common.auth import AuthManager
from common.api_gateway import APIGateway
from common.events import register_all_handlers


class EffiLifeIntegration:
    """
    EffiLife 集成管理器

    负责初始化和协调所有跨模块组件。

    使用方式:
        integration = EffiLifeIntegration()
        integration.initialize()

        # 注册模块
        integration.register_todo_api(todo_api)
        integration.register_plan_api(plan_api)
        integration.register_time_api(time_api)

        # 使用网关
        result = integration.gateway.query_daily_summary()
    """

    def __init__(self, data_root: str = None):
        self.data_root = data_root

        # 核心组件
        self.event_bus = EventBus.get_instance()
        self.data_manager = DataManager.get_instance(data_root)
        self.auth_manager = AuthManager.get_instance()
        self.gateway = APIGateway.get_instance()

        # 事件处理器
        self._handlers = {}
        self._initialized = False

    def initialize(self):
        """初始化集成系统"""
        if self._initialized:
            return

        # 加载数据
        self.data_manager.load()
        self.auth_manager.load()

        # 设置事件日志
        log_dir = self.data_manager.events_dir
        self.event_bus.set_log_file(str(log_dir / 'events.log'))

        # 注册模块数据目录
        project_root = Path(__file__).parent.parent
        self.data_manager.register_module_data_dir(
            'time-helper',
            str(project_root / 'time-helper' / 'data')
        )
        self.data_manager.register_module_data_dir(
            'to-dos',
            str(project_root / 'to-dos' / 'data')
        )
        self.data_manager.register_module_data_dir(
            'plan-helper',
            str(project_root / 'plan-helper' / 'data')
        )

        self._initialized = True

    def register_todo_api(self, todo_api):
        """注册 to-dos 模块 API"""
        self.gateway.register_module('to-dos', todo_api)
        self._register_event_handlers()

    def register_plan_api(self, plan_api):
        """注册 plan-helper 模块 API"""
        self.gateway.register_module('plan-helper', plan_api)
        self._register_event_handlers()

    def register_time_api(self, time_api):
        """注册 time-helper 模块 API"""
        self.gateway.register_module('time-helper', time_api)
        self._register_event_handlers()

    def _register_event_handlers(self):
        """注册事件处理器（当至少一个模块注册后）"""
        if not self._handlers:
            self._handlers = register_all_handlers(
                gateway=self.gateway,
                data_manager=self.data_manager,
                event_bus=self.event_bus,
            )

    def get_stats(self) -> dict:
        """获取集成系统统计"""
        return {
            'modules': self.gateway.list_modules(),
            'event_bus': self.event_bus.get_stats(),
            'data_manager': self.data_manager.get_stats(),
            'auth': self.auth_manager.get_stats(),
        }

    def emit_event(self, event_type: str, source_module: str, data: dict = None):
        """发布事件"""
        user = self.auth_manager.get_current_user()
        user_id = user.id if user else None
        return self.event_bus.emit(
            event_type=event_type,
            source_module=source_module,
            data=data or {},
            user_id=user_id,
        )


# 全局单例
_integration: EffiLifeIntegration = None


def get_integration(data_root: str = None) -> EffiLifeIntegration:
    """获取全局集成实例"""
    global _integration
    if _integration is None:
        _integration = EffiLifeIntegration(data_root)
        _integration.initialize()
    return _integration


def reset_integration():
    """重置全局集成实例（用于测试）"""
    global _integration
    _integration = None
    EventBus.reset_instance()
    DataManager.reset_instance()
    AuthManager.reset_instance()
    APIGateway.reset_instance()
