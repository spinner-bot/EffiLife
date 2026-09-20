"""
to-dos 数据存储服务
负责 todo 数据的持久化读写
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from .types import Todo, Category, Subtask, TodoStatus, Priority
from .utils import IdGenerator, TimeHelper


class TodoStorage:
    """待办事项存储管理器"""

    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化存储服务
        data_dir: 数据存储目录，默认为项目根目录下的 data/todos/
        """
        if data_dir is None:
            # 默认使用 EffLife 共享数据目录
            project_root = Path(__file__).parent.parent.parent.parent
            data_dir = project_root / 'data' / 'todos'
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.todos_file = data_dir / 'todos.json'
        self.categories_file = data_dir / 'categories.json'
        self.archive_dir = data_dir / 'archive'

        # 确保目录存在
        self._ensure_dirs()

        # 内存缓存
        self._todos: List[Todo] = []
        self._categories: List[Category] = []
        self._loaded = False

    def _ensure_dirs(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        """加载所有数据到内存"""
        self._todos = self._load_todos()
        self._categories = self._load_categories()
        self._loaded = True

    def _load_todos(self) -> List[Todo]:
        """从文件加载 todos"""
        if not self.todos_file.exists():
            return []
        try:
            with open(self.todos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Todo.from_dict(item) for item in data]
        except (json.JSONDecodeError, IOError):
            return []

    def _load_categories(self) -> List[Category]:
        """从文件加载分类"""
        if not self.categories_file.exists():
            # 返回默认分类
            return self._default_categories()
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Category.from_dict(item) for item in data]
        except (json.JSONDecodeError, IOError):
            return self._default_categories()

    def _default_categories(self) -> List[Category]:
        """默认分类"""
        return [
            Category(id='default', name='默认', color='#6366f1', icon='circle'),
            Category(id='work', name='工作', color='#3b82f6', icon='briefcase'),
            Category(id='study', name='学习', color='#22c55e', icon='book-open'),
            Category(id='life', name='生活', color='#f59e0b', icon='home'),
            Category(id='health', name='健康', color='#ef4444', icon='heart'),
        ]

    def _save_todos(self):
        """保存 todos 到文件"""
        with open(self.todos_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self._todos], f,
                      ensure_ascii=False, indent=2)

    def _save_categories(self):
        """保存分类到文件"""
        with open(self.categories_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in self._categories], f,
                      ensure_ascii=False, indent=2)

    # ========== Todo 操作 ==========

    def get_all_todos(
        self,
        status: Optional[TodoStatus] = None,
        priority: Optional[Priority] = None,
        category: Optional[str] = None,
    ) -> List[Todo]:
        """获取所有 todos（支持过滤）"""
        if not self._loaded:
            self.load()

        result = self._todos
        if status is not None:
            result = [t for t in result if t.status == status]
        if priority is not None:
            result = [t for t in result if t.priority == priority]
        if category is not None:
            result = [t for t in result if t.category == category]
        return result

    def get_todo_by_id(self, todo_id: str) -> Optional[Todo]:
        """根据 ID 获取 todo"""
        if not self._loaded:
            self.load()
        for t in self._todos:
            if t.id == todo_id:
                return t
        return None

    def create_todo(
        self,
        title: str,
        priority: Priority = Priority.NORMAL,
        category: str = 'default',
        description: Optional[str] = None,
        deadline: Optional[str] = None,
        tags: Optional[list] = None,
        related_plan_id: Optional[str] = None,
        time_estimate: Optional[int] = None,
    ) -> Todo:
        """创建新的待办事项"""
        if not self._loaded:
            self.load()

        now = TimeHelper.now_iso()
        todo_id = IdGenerator.generate_todo_id()

        todo = Todo(
            id=todo_id,
            title=title,
            created_at=now,
            updated_at=now,
            priority=priority,
            category=category,
            description=description,
            deadline=deadline,
            tags=tags or [],
            related_plan_id=related_plan_id,
            time_estimate=time_estimate,
        )

        self._todos.append(todo)
        self._save_todos()
        return todo

    def update_todo(self, todo_id: str, **kwargs) -> Optional[Todo]:
        """更新待办事项"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return None

        # 允许更新的字段
        updatable_fields = {
            'title', 'description', 'deadline', 'priority', 'category',
            'tags', 'related_plan_id', 'time_estimate', 'notes', 'status',
        }

        for key, value in kwargs.items():
            if key in updatable_fields:
                setattr(todo, key, value)

        todo.updated_at = TimeHelper.now_iso()
        self._save_todos()
        return todo

    def delete_todo(self, todo_id: str) -> bool:
        """删除待办事项（移至归档）"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False

        # 归档而不是真正删除
        todo.archive()
        self._save_todos()

        # 同时保存到归档文件
        archive_month = datetime.now().strftime('%Y-%m')
        archive_file = self.archive_dir / archive_month / 'todos.json'
        archive_file.parent.mkdir(parents=True, exist_ok=True)

        archived = []
        if archive_file.exists():
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    archived = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        archived.append(todo.to_dict())
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archived, f, ensure_ascii=False, indent=2)

        return True

    def complete_todo(self, todo_id: str, time_spent: Optional[int] = None) -> Optional[Todo]:
        """标记待办完成"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return None

        todo.complete(time_spent)
        self._save_todos()
        return todo

    def cancel_todo(self, todo_id: str) -> Optional[Todo]:
        """标记待办取消"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return None

        todo.cancel()
        self._save_todos()
        return todo

    # ========== 子任务操作 ==========

    def add_subtask(self, todo_id: str, title: str) -> Optional[Subtask]:
        """添加子任务"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return None

        subtask = Subtask(
            id=IdGenerator.generate_subtask_id(),
            title=title,
        )
        todo.subtasks.append(subtask)
        todo.updated_at = TimeHelper.now_iso()
        self._save_todos()
        return subtask

    def toggle_subtask(self, todo_id: str, subtask_id: str) -> bool:
        """切换子任务完成状态"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False

        for s in todo.subtasks:
            if isinstance(s, Subtask) and s.id == subtask_id:
                s.completed = not s.completed
                if s.completed:
                    s.completed_at = TimeHelper.now_iso()
                else:
                    s.completed_at = None
                break

        todo.updated_at = TimeHelper.now_iso()
        self._save_todos()
        return True

    def delete_subtask(self, todo_id: str, subtask_id: str) -> bool:
        """删除子任务"""
        if not self._loaded:
            self.load()

        todo = self.get_todo_by_id(todo_id)
        if not todo:
            return False

        original_len = len(todo.subtasks)
        todo.subtasks = [s for s in todo.subtasks
                         if not (isinstance(s, Subtask) and s.id == subtask_id)]

        if len(todo.subtasks) < original_len:
            todo.updated_at = TimeHelper.now_iso()
            self._save_todos()
            return True
        return False

    # ========== 分类操作 ==========

    def get_categories(self) -> List[Category]:
        """获取所有分类"""
        if not self._loaded:
            self.load()
        return self._categories

    def get_category_by_id(self, category_id: str) -> Optional[Category]:
        """根据 ID 获取分类"""
        if not self._loaded:
            self.load()
        for c in self._categories:
            if c.id == category_id:
                return c
        return None

    def create_category(
        self,
        name: str,
        color: str = '#6366f1',
        icon: str = 'circle',
        description: Optional[str] = None,
    ) -> Category:
        """创建新分类"""
        if not self._loaded:
            self.load()

        category = Category(
            id=IdGenerator.generate_category_id(),
            name=name,
            color=color,
            icon=icon,
            description=description,
        )
        self._categories.append(category)
        self._save_categories()
        return category

    def update_category(self, category_id: str, **kwargs) -> Optional[Category]:
        """更新分类"""
        if not self._loaded:
            self.load()

        category = self.get_category_by_id(category_id)
        if not category:
            return None

        updatable_fields = {'name', 'color', 'icon', 'description'}
        for key, value in kwargs.items():
            if key in updatable_fields:
                setattr(category, key, value)

        self._save_categories()
        return category

    def delete_category(self, category_id: str) -> bool:
        """删除分类"""
        if not self._loaded:
            self.load()

        original_len = len(self._categories)
        self._categories = [c for c in self._categories if c.id != category_id]

        if len(self._categories) < original_len:
            # 将该分类下的 todos 移至默认分类
            for todo in self._todos:
                if todo.category == category_id:
                    todo.category = 'default'
            self._save_todos()
            self._save_categories()
            return True
        return False

    # ========== 查询与统计 ==========

    def get_overdue_todos(self) -> List[Todo]:
        """获取所有逾期的待办"""
        if not self._loaded:
            self.load()
        return [t for t in self._todos if t.is_overdue()]

    def get_today_todos(self) -> List[Todo]:
        """获取今日到期的待办"""
        if not self._loaded:
            self.load()
        today = TimeHelper.today_str()
        result = []
        for t in self._todos:
            if t.deadline and t.deadline[:10] == today:
                result.append(t)
            elif t.status == TodoStatus.IN_PROGRESS:
                result.append(t)
        return result

    def search_todos(self, keyword: str) -> List[Todo]:
        """搜索待办"""
        if not self._loaded:
            self.load()
        keyword = keyword.lower()
        return [
            t for t in self._todos
            if keyword in t.title.lower()
            or keyword in (t.description or '').lower()
            or any(keyword in tag.lower() for tag in t.tags)
        ]

    def get_stats(self) -> dict:
        """获取统计信息"""
        if not self._loaded:
            self.load()

        total = len(self._todos)
        if total == 0:
            return {
                'total': 0, 'pending': 0, 'in_progress': 0,
                'completed': 0, 'archived': 0, 'cancelled': 0,
                'overdue': 0, 'completion_rate': 0,
                'by_priority': {}, 'by_category': {},
            }

        by_status = {}
        by_priority = {}
        by_category = {}

        for t in self._todos:
            status_val = t.status.value if isinstance(t.status, TodoStatus) else t.status
            priority_val = t.priority.value if isinstance(t.priority, Priority) else t.priority

            by_status[status_val] = by_status.get(status_val, 0) + 1
            by_priority[priority_val] = by_priority.get(priority_val, 0) + 1
            by_category[t.category] = by_category.get(t.category, 0) + 1

        completed = by_status.get('completed', 0)
        # 完成率 = 已完成 / (已完成 + 待处理 + 进行中)
        active = total - by_status.get('archived', 0) - by_status.get('cancelled', 0)
        rate = round(completed / active * 100, 1) if active > 0 else 0

        return {
            'total': total,
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'completed': completed,
            'archived': by_status.get('archived', 0),
            'cancelled': by_status.get('cancelled', 0),
            'overdue': len(self.get_overdue_todos()),
            'completion_rate': rate,
            'by_priority': by_priority,
            'by_category': by_category,
        }
