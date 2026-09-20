"""
EffiLife Common - 跨模块集成层

提供统一的数据格式、API 网关、事件系统和身份认证，
让 time-helper、plan-helper、to-dos 三个模块协同工作。
"""

__version__ = '1.0.0'

from .schemas import SchemaVersion, CrossReference, UnifiedTimestamp
from .data_manager import DataManager
from .event_bus import EventBus, EventType
from .auth import AuthManager, User
