"""
to-dos 数据模型定义
定义待办事项的核心数据结构
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from enum import Enum
import json


class Priority(str, Enum):
    """优先级定义"""
    URGENT_IMPORTANT = 'urgent-important'  # 紧急且重要
    IMPORTANT = 'important'                # 重要
    URGENT = 'urgent'                      # 紧急
    NORMAL = 'normal'                      # 普通


class TodoStatus(str, Enum):
    """待办状态"""
    PENDING = 'pending'           # 待处理
    IN_PROGRESS = 'in-progress'   # 进行中
    COMPLETED = 'completed'       # 已完成
    ARCHIVED = 'archived'         # 已归档
    CANCELLED = 'cancelled'       # 已取消


@dataclass
class Subtask:
    """子任务"""
    id: str
    title: str
    completed: bool = False
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Subtask':
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            completed=data.get('completed', False),
            completed_at=data.get('completed_at')
        )


@dataclass
class Category:
    """分类"""
    id: str
    name: str
    color: str = '#6366f1'
    icon: str = 'circle'
    description: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Category':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            color=data.get('color', '#6366f1'),
            icon=data.get('icon', 'circle'),
            description=data.get('description'),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


class RecurrenceType(str, Enum):
    """重复类型"""
    NONE = 'none'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


@dataclass
class Todo:
    """待办事项核心数据结构"""
    id: str                           # 唯一编号：TODO-YYYYMMDD-XXXX
    title: str                        # 任务标题
    created_at: str                   # 创建时间
    updated_at: str                   # 更新时间
    priority: Priority = Priority.NORMAL
    category: str = 'default'         # 分类 ID
    status: TodoStatus = TodoStatus.PENDING
    description: Optional[str] = None # 详细描述
    deadline: Optional[str] = None    # 截止日期
    completed_at: Optional[str] = None
    tags: list = field(default_factory=list)
    subtasks: list = field(default_factory=list)
    related_plan_id: Optional[str] = None  # 关联 plan-helper
    time_estimate: Optional[int] = None    # 预估时间（分钟）
    time_spent: Optional[int] = None       # 实际花费（分钟）
    notes: Optional[str] = None
    # v0.3.0 新增字段
    recurrence: RecurrenceType = RecurrenceType.NONE
    deadline_warning_days: int = 3         # 提前几天警告
    sort_order: int = 0                    # 自定义排序
    pinned: bool = False                   # 是否置顶

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'deadline': self.deadline,
            'priority': self.priority.value if isinstance(self.priority, Priority) else self.priority,
            'category': self.category,
            'status': self.status.value if isinstance(self.status, TodoStatus) else self.status,
            'completed_at': self.completed_at,
            'tags': self.tags,
            'subtasks': [
                s.to_dict() if isinstance(s, Subtask) else s
                for s in self.subtasks
            ],
            'related_plan_id': self.related_plan_id,
            'time_estimate': self.time_estimate,
            'time_spent': self.time_spent,
            'notes': self.notes,
            'recurrence': self.recurrence.value if isinstance(self.recurrence, RecurrenceType) else self.recurrence,
            'deadline_warning_days': self.deadline_warning_days,
            'sort_order': self.sort_order,
            'pinned': self.pinned,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Todo':
        """从字典创建"""
        subtasks_data = data.get('subtasks', [])
        subtasks = []
        for s in subtasks_data:
            if isinstance(s, dict):
                subtasks.append(Subtask.from_dict(s))
            else:
                subtasks.append(s)

        priority = data.get('priority', 'normal')
        if isinstance(priority, str):
            priority = Priority(priority)

        status = data.get('status', 'pending')
        if isinstance(status, str):
            status = TodoStatus(status)

        recurrence = data.get('recurrence', 'none')
        if isinstance(recurrence, str):
            try:
                recurrence = RecurrenceType(recurrence)
            except ValueError:
                recurrence = RecurrenceType.NONE

        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            description=data.get('description'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            deadline=data.get('deadline'),
            priority=priority,
            category=data.get('category', 'default'),
            status=status,
            completed_at=data.get('completed_at'),
            tags=data.get('tags', []),
            subtasks=subtasks,
            related_plan_id=data.get('related_plan_id'),
            time_estimate=data.get('time_estimate'),
            time_spent=data.get('time_spent'),
            notes=data.get('notes'),
            recurrence=recurrence,
            deadline_warning_days=data.get('deadline_warning_days', 3),
            sort_order=data.get('sort_order', 0),
            pinned=data.get('pinned', False),
        )

    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if not self.deadline or self.status in (TodoStatus.COMPLETED, TodoStatus.CANCELLED):
            return False
        try:
            deadline_dt = datetime.fromisoformat(self.deadline)
            return datetime.now() > deadline_dt
        except ValueError:
            return False

    def needs_warning(self) -> bool:
        """检查是否需要截止提醒（在 deadline_warning_days 天内到期）"""
        if not self.deadline or self.status in (TodoStatus.COMPLETED, TodoStatus.CANCELLED):
            return False
        try:
            deadline_dt = datetime.fromisoformat(self.deadline)
            now = datetime.now()
            diff = (deadline_dt - now).days
            return 0 <= diff <= self.deadline_warning_days
        except ValueError:
            return False

    def toggle_pin(self):
        """切换置顶状态"""
        self.pinned = not self.pinned
        self.updated_at = datetime.now().isoformat()

    def complete(self, time_spent: Optional[int] = None):
        """标记完成"""
        now = datetime.now()
        self.status = TodoStatus.COMPLETED
        self.completed_at = now.isoformat()
        self.updated_at = now.isoformat()
        if time_spent is not None:
            self.time_spent = time_spent

    def cancel(self):
        """标记取消"""
        self.status = TodoStatus.CANCELLED
        self.updated_at = datetime.now().isoformat()

    def archive(self):
        """归档"""
        self.status = TodoStatus.ARCHIVED
        self.updated_at = datetime.now().isoformat()

    def progress(self) -> float:
        """计算进度百分比（基于子任务）"""
        if not self.subtasks:
            return 0.0
        completed = sum(1 for s in self.subtasks if isinstance(s, Subtask) and s.completed)
        return round(completed / len(self.subtasks) * 100, 1)


# 优先级的中文显示名
PRIORITY_LABELS = {
    Priority.URGENT_IMPORTANT: '紧急且重要',
    Priority.IMPORTANT: '重要',
    Priority.URGENT: '紧急',
    Priority.NORMAL: '普通',
}

# 状态的中文显示名
STATUS_LABELS = {
    TodoStatus.PENDING: '待处理',
    TodoStatus.IN_PROGRESS: '进行中',
    TodoStatus.COMPLETED: '已完成',
    TodoStatus.ARCHIVED: '已归档',
    TodoStatus.CANCELLED: '已取消',
}
