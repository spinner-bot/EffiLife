"""
    ============ modules/manager.py ============
    TodoManager：待办事项管理器的核心 API 门面
        by spinner-bot
"""

from datetime import datetime
from pathlib import Path

from .todo import (
    Todo, now_iso, today_str,
    PRIORITY_NONE, PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_URGENT,
    PRIORITY_NAMES, STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED,
)
from . import storage


class TodoManager:
    """
    待办事项管理器。
    提供 CRUD、状态切换、查询、统计等全部 API。
    """

    def __init__(self, data_dir: str | Path = None):
        self.data_dir = Path(data_dir) if data_dir else storage.DEFAULT_DATA_DIR
        self._registry = None
        self._todos = {}  # id -> Todo 内存缓存
        self._loaded = False

    # ------------------------------------------
    # 初始化与加载
    # ------------------------------------------

    def init(self) -> dict:
        """初始化数据目录"""
        return storage.init_data_dir(self.data_dir)

    def _ensure_loaded(self) -> None:
        """确保数据已加载到内存"""
        if not self._loaded:
            self.reload()

    def reload(self) -> None:
        """从磁盘重新加载所有数据"""
        self._registry = storage.load_registry(self.data_dir)
        self._todos = {}
        for todo in storage.load_all_todos(self.data_dir):
            self._todos[todo.id] = todo
        self._loaded = True

    def _save_registry(self) -> None:
        storage.save_registry(self._registry, self.data_dir)

    # ------------------------------------------
    # 创建
    # ------------------------------------------

    def create(self, title: str, priority: int = PRIORITY_MEDIUM, **kwargs) -> Todo:
        """
        创建新待办事项。
        可选参数：description, category, tags, due_date, parent_id
        """
        self._ensure_loaded()

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        # 生成 ID
        todo_id = storage.generate_id(self._registry)
        storage.increment_id(self._registry)

        # 处理子任务关系
        parent_id = kwargs.get("parent_id")
        if parent_id:
            if parent_id not in self._todos:
                raise ValueError(f"Parent todo not found: {parent_id}")

        todo = Todo(
            id=todo_id,
            title=title.strip(),
            priority=priority,
            **kwargs,
        )

        # 保存
        storage.save_todo(todo, self.data_dir)
        self._todos[todo.id] = todo

        # 更新父任务的子任务列表
        if parent_id:
            parent = self._todos[parent_id]
            parent.add_sub(todo_id)
            storage.save_todo(parent, self.data_dir)

        # 更新注册表
        self._registry["active_ids"].append(todo_id)
        self._registry["stats"]["total_created"] = self._registry["stats"].get("total_created", 0) + 1
        self._save_registry()

        return todo

    # ------------------------------------------
    # 读取
    # ------------------------------------------

    def get(self, todo_id: str) -> Todo | None:
        """获取单个 todo"""
        self._ensure_loaded()
        return self._todos.get(todo_id)

    def get_or_raise(self, todo_id: str) -> Todo:
        """获取单个 todo，不存在则抛异常"""
        todo = self.get(todo_id)
        if not todo:
            raise ValueError(f"Todo not found: {todo_id}")
        return todo

    # ------------------------------------------
    # 更新
    # ------------------------------------------

    def update(self, todo_id: str, **fields) -> Todo:
        """更新 todo 字段"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        todo.update(**fields)
        storage.save_todo(todo, self.data_dir)
        return todo

    def delete(self, todo_id: str) -> bool:
        """删除 todo（硬删除）"""
        self._ensure_loaded()
        todo = self.get(todo_id)
        if not todo:
            return False

        # 如果有子任务，先解除关联
        for sub_id in todo.sub_ids:
            sub = self._todos.get(sub_id)
            if sub:
                sub.parent_id = None
                storage.save_todo(sub, self.data_dir)

        # 从父任务中移除
        if todo.parent_id:
            parent = self._todos.get(todo.parent_id)
            if parent:
                parent.remove_sub(todo_id)
                storage.save_todo(parent, self.data_dir)

        # 删除文件
        storage.delete_todo_file(todo_id, self.data_dir)
        del self._todos[todo_id]

        # 更新注册表
        if todo_id in self._registry["active_ids"]:
            self._registry["active_ids"].remove(todo_id)
        if todo_id in self._registry["archived_ids"]:
            self._registry["archived_ids"].remove(todo_id)
        self._save_registry()

        return True

    # ------------------------------------------
    # 状态操作
    # ------------------------------------------

    def start(self, todo_id: str) -> Todo:
        """标记为进行中"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        todo.start()
        storage.save_todo(todo, self.data_dir)
        return todo

    def complete(self, todo_id: str) -> Todo:
        """标记为完成"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        todo.complete()
        storage.save_todo(todo, self.data_dir)

        # 更新注册表统计
        self._registry["stats"]["total_completed"] = self._registry["stats"].get("total_completed", 0) + 1

        # 自动归档（如果配置开启）
        config = storage.load_config(self.data_dir)
        if config.get("auto_archive_on_complete"):
            self.archive(todo_id)
        else:
            self._save_registry()

        return todo

    def cancel(self, todo_id: str) -> Todo:
        """取消任务"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        todo.cancel()
        storage.save_todo(todo, self.data_dir)
        self._registry["stats"]["total_cancelled"] = self._registry["stats"].get("total_cancelled", 0) + 1
        self._save_registry()
        return todo

    def reopen(self, todo_id: str) -> Todo:
        """重新打开"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        todo.reopen()
        storage.save_todo(todo, self.data_dir)

        # 如果在归档中，需要移回活跃
        if todo.archived:
            self._unarchive(todo)

        return todo

    # ------------------------------------------
    # 归档
    # ------------------------------------------

    def archive(self, todo_id: str) -> Todo:
        """归档 todo"""
        self._ensure_loaded()
        todo = self.get_or_raise(todo_id)
        storage.archive_todo(todo, self.data_dir)

        # 更新注册表
        if todo_id in self._registry["active_ids"]:
            self._registry["active_ids"].remove(todo_id)
        self._registry["archived_ids"].append(todo_id)
        self._save_registry()

        # 从内存移除
        del self._todos[todo_id]

        return todo

    def _unarchive(self, todo: Todo) -> None:
        """将 todo 从归档移回活跃"""
        todo.archived = False
        storage.save_todo(todo, self.data_dir)
        storage.delete_todo_file(todo.id, self.data_dir)  # 删除归档文件

        # 从归档目录中也删
        archive_dir = self.data_dir / storage.ARCHIVE_DIR
        for month_dir in archive_dir.iterdir():
            if month_dir.is_dir():
                archived_file = month_dir / f"{todo.id}.json"
                if archived_file.exists():
                    import os
                    os.remove(archived_file)

        if todo.id in self._registry["archived_ids"]:
            self._registry["archived_ids"].remove(todo.id)
        if todo.id not in self._registry["active_ids"]:
            self._registry["active_ids"].append(todo.id)
        self._todos[todo.id] = todo
        self._save_registry()

    # ------------------------------------------
    # 查询
    # ------------------------------------------

    def list_all(self, status: str = None, priority: int = None, category: str = None) -> list[Todo]:
        """列出所有 todo，可按条件筛选"""
        self._ensure_loaded()
        results = list(self._todos.values())

        if status:
            results = [t for t in results if t.status == status]
        if priority is not None:
            results = [t for t in results if t.priority == priority]
        if category:
            results = [t for t in results if t.category == category]

        return results

    def list_active(self) -> list[Todo]:
        """列出所有未归档的 todo"""
        self._ensure_loaded()
        return [t for t in self._todos.values() if not t.archived]

    def list_overdue(self) -> list[Todo]:
        """列出已过期任务"""
        self._ensure_loaded()
        return [t for t in self._todos.values() if t.is_overdue()]

    def list_by_category(self, category: str) -> list[Todo]:
        """按分类列出"""
        return self.list_all(category=category)

    def list_by_priority(self, priority: int) -> list[Todo]:
        """按优先级列出"""
        return self.list_all(priority=priority)

    def list_archived(self, month: str = None) -> list[Todo]:
        """列出已归档的 todo"""
        return storage.load_archived_todos(month, self.data_dir)

    def search(self, query: str) -> list[Todo]:
        """全文搜索（标题 + 描述 + 标签）"""
        self._ensure_loaded()
        q = query.lower().strip()
        if not q:
            return []
        results = []
        for todo in self._todos.values():
            if (q in todo.title.lower()
                    or q in todo.description.lower()
                    or any(q in tag.lower() for tag in todo.tags)):
                results.append(todo)
        return results

    # ------------------------------------------
    # 子任务
    # ------------------------------------------

    def add_subtask(self, parent_id: str, title: str, **kwargs) -> Todo:
        """添加子任务"""
        kwargs["parent_id"] = parent_id
        return self.create(title, **kwargs)

    def list_subtasks(self, parent_id: str) -> list[Todo]:
        """列出某任务的所有子任务"""
        self._ensure_loaded()
        parent = self.get_or_raise(parent_id)
        return [self._todos[sid] for sid in parent.sub_ids if sid in self._todos]

    # ------------------------------------------
    # 分类管理
    # ------------------------------------------

    def add_category(self, name: str, color: str = None, icon: str = None) -> dict:
        """添加分类"""
        categories = storage.load_categories(self.data_dir)
        for cat in categories["categories"]:
            if cat["name"] == name:
                raise ValueError(f"Category already exists: {name}")
        new_cat = {"name": name, "color": color or "#6B7280", "icon": icon or "tag"}
        categories["categories"].append(new_cat)
        storage.save_categories(categories, self.data_dir)
        return new_cat

    def remove_category(self, name: str) -> bool:
        """删除分类"""
        categories = storage.load_categories(self.data_dir)
        original = len(categories["categories"])
        categories["categories"] = [c for c in categories["categories"] if c["name"] != name]
        if len(categories["categories"]) < original:
            storage.save_categories(categories, self.data_dir)
            return True
        return False

    def list_categories(self) -> list[dict]:
        """列出所有分类"""
        return storage.load_categories(self.data_dir)["categories"]

    # ------------------------------------------
    # 统计
    # ------------------------------------------

    def stats(self) -> dict:
        """获取统计信息"""
        self._ensure_loaded()
        all_todos = list(self._todos.values())
        return {
            "total": len(all_todos),
            "pending": len([t for t in all_todos if t.status == STATUS_PENDING]),
            "in_progress": len([t for t in all_todos if t.status == STATUS_IN_PROGRESS]),
            "completed": len([t for t in all_todos if t.status == STATUS_COMPLETED]),
            "cancelled": len([t for t in all_todos if t.status == STATUS_CANCELLED]),
            "overdue": len([t for t in all_todos if t.is_overdue()]),
            "with_due_date": len([t for t in all_todos if t.due_date]),
            "archived": len(self._registry.get("archived_ids", [])),
            "total_created": self._registry["stats"].get("total_created", 0),
            "total_completed_all": self._registry["stats"].get("total_completed", 0),
            "total_cancelled_all": self._registry["stats"].get("total_cancelled", 0),
        }

    def completion_rate(self) -> float:
        """完成率"""
        s = self.stats()
        total_done = s["completed"] + s["cancelled"]
        if s["total"] == 0:
            return 0.0
        return round(s["completed"] / s["total"] * 100, 1)

    # ------------------------------------------
    # 排序辅助
    # ------------------------------------------

    @staticmethod
    def sort_todos(todos: list[Todo], by: str = "created_at", order: str = "desc") -> list[Todo]:
        """排序 todo 列表"""
        reverse = (order == "desc")
        if by == "priority":
            return sorted(todos, key=lambda t: t.priority, reverse=reverse)
        elif by == "due_date":
            return sorted(todos, key=lambda t: t.due_date or "9999-12-31", reverse=reverse)
        elif by == "title":
            return sorted(todos, key=lambda t: t.title.lower(), reverse=reverse)
        elif by == "status":
            return sorted(todos, key=lambda t: t.status, reverse=reverse)
        else:  # created_at / updated_at
            return sorted(todos, key=lambda t: getattr(t, by, t.created_at), reverse=reverse)

    # ------------------------------------------
    # 跨模块接口（预留）
    # ------------------------------------------

    def get_tasks_for_plan(self, plan_id: str) -> list[Todo]:
        """获取与某计划关联的任务（预留）"""
        # TODO: 实现 plan_id 关联逻辑
        return []

    def link_to_plan(self, todo_id: str, plan_id: str) -> bool:
        """将任务关联到计划（预留）"""
        # TODO: 实现关联逻辑
        return False

    def get_time_spent(self, todo_id: str) -> dict:
        """获取任务耗时（预留，与 time-helper 联动）"""
        # TODO: 从 time-helper 获取数据
        return {"todo_id": todo_id, "total_minutes": 0}

    def log_time(self, todo_id: str, duration: int) -> bool:
        """记录任务耗时（预留，与 time-helper 联动）"""
        # TODO: 写入 time-helper 数据
        return False
