"""
统一数据模型

定义三个模块共享的数据结构，用于跨模块数据交换。
各模块内部仍使用自己的数据结构，但通过适配器与统一模型互转。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from .core import UnifiedTimestamp, SchemaVersion


@dataclass
class UnifiedCategory:
    """统一分类模型"""
    id: str
    name: str
    color: str = '#6366f1'
    icon: str = 'circle'
    description: Optional[str] = None
    module: str = 'to-dos'
    created_at: str = field(default_factory=UnifiedTimestamp.now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'description': self.description,
            'module': self.module,
            'created_at': self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UnifiedCategory':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            color=data.get('color', '#6366f1'),
            icon=data.get('icon', 'circle'),
            description=data.get('description'),
            module=data.get('module', 'to-dos'),
            created_at=data.get('created_at', UnifiedTimestamp.now()),
        )


@dataclass
class UnifiedPlan:
    """
    统一计划模型

    聚合 plan-helper 的 Plan 结构和 time-helper 的 day plan。
    """
    id: str
    name: str
    module: str = 'plan-helper'        # 来源模块
    plan_type: str = 'standard'        # 'standard' | 'day-split' | 'day-alloc'
    date: Optional[str] = None         # YYYY-MM-DD
    sections: list = field(default_factory=list)
    items: list = field(default_factory=list)    # 日计划的时间类别
    bg_tag: str = ''
    color: list = field(default_factory=lambda: [128, 128, 128])
    total_tasks: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0
    estimated_minutes: float = 0.0
    created_at: str = field(default_factory=UnifiedTimestamp.now)
    updated_at: str = field(default_factory=UnifiedTimestamp.now)
    schema_version: str = SchemaVersion.CURRENT.value

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'module': self.module,
            'plan_type': self.plan_type,
            'date': self.date,
            'sections': self.sections,
            'items': self.items,
            'bg_tag': self.bg_tag,
            'color': self.color,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'progress_percentage': self.progress_percentage,
            'estimated_minutes': self.estimated_minutes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'schema_version': self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UnifiedPlan':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            module=data.get('module', 'plan-helper'),
            plan_type=data.get('plan_type', 'standard'),
            date=data.get('date'),
            sections=data.get('sections', []),
            items=data.get('items', []),
            bg_tag=data.get('bg_tag', ''),
            color=data.get('color', [128, 128, 128]),
            total_tasks=data.get('total_tasks', 0),
            completed_tasks=data.get('completed_tasks', 0),
            progress_percentage=data.get('progress_percentage', 0.0),
            estimated_minutes=data.get('estimated_minutes', 0.0),
            created_at=data.get('created_at', UnifiedTimestamp.now()),
            updated_at=data.get('updated_at', UnifiedTimestamp.now()),
            schema_version=data.get('schema_version', SchemaVersion.CURRENT.value),
        )


@dataclass
class UnifiedTodo:
    """
    统一待办模型

    与 to-dos 模块的 Todo 结构兼容，增加跨模块引用字段。
    """
    id: str
    title: str
    created_at: str = field(default_factory=UnifiedTimestamp.now)
    updated_at: str = field(default_factory=UnifiedTimestamp.now)
    priority: str = 'normal'           # urgent-important | important | urgent | normal
    category: str = 'default'
    status: str = 'pending'            # pending | in-progress | completed | archived | cancelled
    description: Optional[str] = None
    deadline: Optional[str] = None
    completed_at: Optional[str] = None
    tags: list = field(default_factory=list)
    subtasks: list = field(default_factory=list)
    related_plan_id: Optional[str] = None
    related_time_record_ids: list = field(default_factory=list)
    time_estimate: Optional[int] = None     # 预估分钟
    time_spent: Optional[int] = None        # 实际分钟
    notes: Optional[str] = None
    recurrence: str = 'none'
    deadline_warning_days: int = 3
    sort_order: int = 0
    pinned: bool = False
    schema_version: str = SchemaVersion.CURRENT.value

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'priority': self.priority,
            'category': self.category,
            'status': self.status,
            'description': self.description,
            'deadline': self.deadline,
            'completed_at': self.completed_at,
            'tags': self.tags,
            'subtasks': self.subtasks,
            'related_plan_id': self.related_plan_id,
            'related_time_record_ids': self.related_time_record_ids,
            'time_estimate': self.time_estimate,
            'time_spent': self.time_spent,
            'notes': self.notes,
            'recurrence': self.recurrence,
            'deadline_warning_days': self.deadline_warning_days,
            'sort_order': self.sort_order,
            'pinned': self.pinned,
            'schema_version': self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UnifiedTodo':
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            created_at=data.get('created_at', UnifiedTimestamp.now()),
            updated_at=data.get('updated_at', UnifiedTimestamp.now()),
            priority=data.get('priority', 'normal'),
            category=data.get('category', 'default'),
            status=data.get('status', 'pending'),
            description=data.get('description'),
            deadline=data.get('deadline'),
            completed_at=data.get('completed_at'),
            tags=data.get('tags', []),
            subtasks=data.get('subtasks', []),
            related_plan_id=data.get('related_plan_id'),
            related_time_record_ids=data.get('related_time_record_ids', []),
            time_estimate=data.get('time_estimate'),
            time_spent=data.get('time_spent'),
            notes=data.get('notes'),
            recurrence=data.get('recurrence', 'none'),
            deadline_warning_days=data.get('deadline_warning_days', 3),
            sort_order=data.get('sort_order', 0),
            pinned=data.get('pinned', False),
            schema_version=data.get('schema_version', SchemaVersion.CURRENT.value),
        )


@dataclass
class UnifiedTimeRecord:
    """
    统一时间记录模型

    与 time-helper 的 record 结构兼容，增加跨模块引用字段。
    """
    id: str
    date: str                         # YYYY-MM-DD
    start_time: str                   # HH:MM
    end_time: str                     # HH:MM
    duration_hours: float             # 时长（小时）
    content: str = ''
    tag: str = ''
    related_todo_id: Optional[str] = None
    related_plan_id: Optional[str] = None
    created_at: str = field(default_factory=UnifiedTimestamp.now)
    schema_version: str = SchemaVersion.CURRENT.value

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'date': self.date,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_hours': self.duration_hours,
            'content': self.content,
            'tag': self.tag,
            'related_todo_id': self.related_todo_id,
            'related_plan_id': self.related_plan_id,
            'created_at': self.created_at,
            'schema_version': self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UnifiedTimeRecord':
        return cls(
            id=data.get('id', ''),
            date=data.get('date', ''),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time', ''),
            duration_hours=data.get('duration_hours', 0),
            content=data.get('content', ''),
            tag=data.get('tag', ''),
            related_todo_id=data.get('related_todo_id'),
            related_plan_id=data.get('related_plan_id'),
            created_at=data.get('created_at', UnifiedTimestamp.now()),
            schema_version=data.get('schema_version', SchemaVersion.CURRENT.value),
        )


@dataclass
class UnifiedUser:
    """统一用户模型"""
    id: str
    username: str
    display_name: str = ''
    avatar: str = ''
    created_at: str = field(default_factory=UnifiedTimestamp.now)
    last_login: Optional[str] = None
    preferences: dict = field(default_factory=dict)
    schema_version: str = SchemaVersion.CURRENT.value

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'avatar': self.avatar,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'preferences': self.preferences,
            'schema_version': self.schema_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UnifiedUser':
        return cls(
            id=data.get('id', ''),
            username=data.get('username', ''),
            display_name=data.get('display_name', ''),
            avatar=data.get('avatar', ''),
            created_at=data.get('created_at', UnifiedTimestamp.now()),
            last_login=data.get('last_login'),
            preferences=data.get('preferences', {}),
            schema_version=data.get('schema_version', SchemaVersion.CURRENT.value),
        )
