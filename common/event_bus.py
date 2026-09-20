"""
事件总线 - 跨模块通信系统

提供发布/订阅模式的事件系统，让模块之间可以松耦合地通信。
例如：当 todo 完成时，自动通知 time-helper 记录时间。
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field, asdict


class EventType(str, Enum):
    """事件类型定义"""
    # Plan 事件
    PLAN_CREATED = 'plan.created'
    PLAN_UPDATED = 'plan.updated'
    PLAN_DELETED = 'plan.deleted'
    PLAN_COMPLETED = 'plan.completed'
    PLAN_TASK_ADDED = 'plan.task_added'
    PLAN_TASK_COMPLETED = 'plan.task_completed'

    # Todo 事件
    TODO_CREATED = 'todo.created'
    TODO_UPDATED = 'todo.updated'
    TODO_COMPLETED = 'todo.completed'
    TODO_CANCELLED = 'todo.cancelled'
    TODO_ARCHIVED = 'todo.archived'
    TODO_SUBTASK_COMPLETED = 'todo.subtask_completed'

    # Time 事件
    TIME_RECORD_CREATED = 'time.record_created'
    TIME_RECORD_UPDATED = 'time.record_updated'
    TIME_RECORD_DELETED = 'time.record_deleted'

    # Auth 事件
    USER_LOGGED_IN = 'user.logged_in'
    USER_LOGGED_OUT = 'user.logged_out'
    USER_CREATED = 'user.created'

    # 集成事件
    INTEGRATION_SYNC = 'integration.sync'
    INTEGRATION_ERROR = 'integration.error'


@dataclass
class Event:
    """事件对象"""
    type: str                    # 事件类型
    source_module: str           # 来源模块
    data: dict = field(default_factory=dict)
    event_id: str = ''
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: Optional[str] = None

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id(self) % 10000:04d}"

    def to_dict(self) -> dict:
        return {
            'type': self.type,
            'source_module': self.source_module,
            'data': self.data,
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'user_id': self.user_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        return cls(
            type=data.get('type', ''),
            source_module=data.get('source_module', ''),
            data=data.get('data', {}),
            event_id=data.get('event_id', ''),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            user_id=data.get('user_id'),
        )


# 事件处理器类型
EventHandler = Callable[[Event], None]


class EventBus:
    """
    事件总线

    支持同步事件发布和订阅。模块可以注册处理器来响应其他模块的事件。
    """

    _instance = None

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_log: List[Event] = []
        self._max_log_size = 1000
        self._log_file: Optional[Path] = None

    @classmethod
    def get_instance(cls) -> 'EventBus':
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        cls._instance = None

    def set_log_file(self, path: str):
        """设置事件日志文件"""
        self._log_file = Path(path)
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    def subscribe(self, event_type: str, handler: EventHandler):
        """
        订阅事件

        Args:
            event_type: 事件类型（支持通配符 '*'）
            handler: 处理函数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消订阅"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    def publish(self, event: Event):
        """
        发布事件

        触发所有匹配的处理器，支持通配符匹配。
        """
        # 记录事件
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

        # 写入日志文件
        if self._log_file:
            self._append_log(event)

        # 触发精确匹配的处理器
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    # 不因处理器异常中断事件传播
                    print(f"[EventBus] Handler error for {event.type}: {e}")

        # 触发通配符处理器
        if '*' in self._handlers:
            for handler in self._handlers['*']:
                try:
                    handler(event)
                except Exception as e:
                    print(f"[EventBus] Wildcard handler error: {e}")

    def emit(
        self,
        event_type: str,
        source_module: str,
        data: Optional[dict] = None,
        user_id: Optional[str] = None,
    ) -> Event:
        """
        快捷发布事件

        Args:
            event_type: 事件类型
            source_module: 来源模块
            data: 事件数据
            user_id: 用户 ID
        Returns:
            创建的 Event 对象
        """
        event = Event(
            type=event_type,
            source_module=source_module,
            data=data or {},
            user_id=user_id,
        )
        self.publish(event)
        return event

    def get_event_log(self, limit: int = 50) -> List[Event]:
        """获取最近的事件日志"""
        return self._event_log[-limit:]

    def get_events_by_type(self, event_type: str) -> List[Event]:
        """按类型筛选事件"""
        return [e for e in self._event_log if e.type == event_type]

    def get_events_by_module(self, module: str) -> List[Event]:
        """按模块筛选事件"""
        return [e for e in self._event_log if e.source_module == module]

    def clear_log(self):
        """清空事件日志"""
        self._event_log.clear()

    def _append_log(self, event: Event):
        """追加到日志文件"""
        try:
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + '\n')
        except IOError:
            pass

    def get_stats(self) -> dict:
        """获取事件统计"""
        by_type = {}
        by_module = {}
        for e in self._event_log:
            by_type[e.type] = by_type.get(e.type, 0) + 1
            by_module[e.source_module] = by_module.get(e.source_module, 0) + 1
        return {
            'total_events': len(self._event_log),
            'by_type': by_type,
            'by_module': by_module,
            'subscribed_types': list(self._handlers.keys()),
        }
