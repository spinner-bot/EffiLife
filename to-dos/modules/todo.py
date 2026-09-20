"""
    ============ modules/todo.py ============
    Todo 数据模型：定义单个待办事项的结构与操作
        by spinner-bot
"""

from datetime import datetime
import json
from pathlib import Path
import copy

# ==========================================
# 常量定义
# ==========================================

PRIORITY_NONE = 0
PRIORITY_LOW = 1
PRIORITY_MEDIUM = 2
PRIORITY_HIGH = 3
PRIORITY_URGENT = 4

PRIORITY_NAMES = {
    0: "none",
    1: "low",
    2: "medium",
    3: "high",
    4: "urgent",
}

STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_CANCELLED = "cancelled"

VALID_STATUSES = {STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED}

DEFAULT_CATEGORIES = ["work", "study", "life", "other"]

# ==========================================


def now_iso() -> str:
    """返回当前时间的 ISO 8601 字符串（不含微秒）"""
    return datetime.now().replace(microsecond=0).isoformat()


def today_str() -> str:
    """返回今日日期 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


class Todo:
    """单个待办事项"""

    def __init__(self, id: str, title: str, priority: int = PRIORITY_MEDIUM, **kwargs):
        if not id.startswith("td_"):
            raise ValueError(f"Invalid todo id format: {id}")

        self.id = id
        self.title = title
        self.priority = self._validate_priority(priority)
        self.description = kwargs.get("description", "")
        self.category = kwargs.get("category", "")
        self.tags = list(kwargs.get("tags", []))
        self.status = self._validate_status(kwargs.get("status", STATUS_PENDING))
        self.created_at = kwargs.get("created_at", now_iso())
        self.updated_at = kwargs.get("updated_at", self.created_at)
        self.due_date = kwargs.get("due_date", None)
        self.completed_at = kwargs.get("completed_at", None)
        self.archived = kwargs.get("archived", False)
        self.parent_id = kwargs.get("parent_id", None)
        self.sub_ids = list(kwargs.get("sub_ids", []))

    # ------------------------------------------
    # 校验
    # ------------------------------------------

    @staticmethod
    def _validate_priority(priority: int) -> int:
        if priority not in PRIORITY_NAMES:
            raise ValueError(f"Invalid priority: {priority}. Must be 0-4.")
        return priority

    @staticmethod
    def _validate_status(status: str) -> str:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}. Must be one of {VALID_STATUSES}")
        return status

    # ------------------------------------------
    # 状态操作
    # ------------------------------------------

    def start(self) -> "Todo":
        """标记为进行中"""
        if self.status in (STATUS_COMPLETED, STATUS_CANCELLED):
            raise ValueError(f"Cannot start a {self.status} todo")
        self.status = STATUS_IN_PROGRESS
        self.updated_at = now_iso()
        return self

    def complete(self) -> "Todo":
        """标记为完成"""
        self.status = STATUS_COMPLETED
        self.completed_at = now_iso()
        self.updated_at = self.completed_at
        return self

    def cancel(self) -> "Todo":
        """标记为取消"""
        if self.status == STATUS_COMPLETED:
            raise ValueError("Cannot cancel a completed todo")
        self.status = STATUS_CANCELLED
        self.updated_at = now_iso()
        return self

    def reopen(self) -> "Todo":
        """重新打开"""
        if self.status not in (STATUS_COMPLETED, STATUS_CANCELLED):
            raise ValueError(f"Cannot reopen a {self.status} todo")
        self.status = STATUS_PENDING
        self.completed_at = None
        self.updated_at = now_iso()
        return self

    # ------------------------------------------
    # 字段更新
    # ------------------------------------------

    def update(self, **fields) -> "Todo":
        """批量更新字段"""
        allowed = {
            "title", "description", "priority", "category", "tags",
            "due_date", "parent_id",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise ValueError(f"Cannot update field: {key}")
            if key == "priority":
                value = self._validate_priority(value)
            setattr(self, key, value)
        self.updated_at = now_iso()
        return self

    # ------------------------------------------
    # 子任务管理
    # ------------------------------------------

    def add_sub(self, sub_id: str) -> "Todo":
        """记录一个子任务 ID"""
        if sub_id not in self.sub_ids:
            self.sub_ids.append(sub_id)
            self.updated_at = now_iso()
        return self

    def remove_sub(self, sub_id: str) -> "Todo":
        """移除一个子任务 ID"""
        if sub_id in self.sub_ids:
            self.sub_ids.remove(sub_id)
            self.updated_at = now_iso()
        return self

    # ------------------------------------------
    # 查询辅助
    # ------------------------------------------

    def is_overdue(self) -> bool:
        """检查是否已过期（有截止日期且已过）"""
        if not self.due_date:
            return False
        if self.status in (STATUS_COMPLETED, STATUS_CANCELLED):
            return False
        return self.due_date < today_str()

    def days_until_due(self) -> int | None:
        """距离截止日期还有多少天（负数表示已过期）"""
        if not self.due_date:
            return None
        due = datetime.strptime(self.due_date, "%Y-%m-%d").date()
        today = datetime.now().date()
        return (due - today).days

    # ------------------------------------------
    # 序列化
    # ------------------------------------------

    def to_dict(self) -> dict:
        """转为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "tags": self.tags,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "due_date": self.due_date,
            "completed_at": self.completed_at,
            "archived": self.archived,
            "parent_id": self.parent_id,
            "sub_ids": self.sub_ids,
        }

    def to_json(self, indent: int = 2) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @staticmethod
    def from_dict(data: dict) -> "Todo":
        """从字典构建"""
        return Todo(
            id=data["id"],
            title=data["title"],
            priority=data.get("priority", PRIORITY_MEDIUM),
            description=data.get("description", ""),
            category=data.get("category", ""),
            tags=data.get("tags", []),
            status=data.get("status", STATUS_PENDING),
            created_at=data.get("created_at", now_iso()),
            updated_at=data.get("updated_at", data.get("created_at", now_iso())),
            due_date=data.get("due_date"),
            completed_at=data.get("completed_at"),
            archived=data.get("archived", False),
            parent_id=data.get("parent_id"),
            sub_ids=data.get("sub_ids", []),
        )

    @staticmethod
    def from_json(json_str: str) -> "Todo":
        """从 JSON 字符串构建"""
        return Todo.from_dict(json.loads(json_str))

    def save(self, path: str | Path) -> str:
        """保存到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return self.id

    @staticmethod
    def load(path: str | Path) -> "Todo":
        """从文件加载"""
        with open(path, "r", encoding="utf-8") as f:
            return Todo.from_json(f.read())

    # ------------------------------------------
    # 显示
    # ------------------------------------------

    def __repr__(self) -> str:
        return f"Todo({self.id}, '{self.title}', status={self.status}, priority={self.priority})"

    def summary(self) -> str:
        """返回一行摘要"""
        pri = PRIORITY_NAMES.get(self.priority, "?")
        due = self.due_date or "no due"
        overdue = " [OVERDUE]" if self.is_overdue() else ""
        return f"[{self.id}] {self.title} | pri={pri} | due={due} | {self.status}{overdue}"
