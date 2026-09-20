"""
to-dos API 服务层
提供统一的 API 接口，支持未来与 time-helper、plan-helper 模块互通
"""

from typing import List, Optional, Dict, Any
from .storage import TodoStorage
from .types import (
    Todo, Subtask, Category,
    Priority, TodoStatus,
)
from .utils import TimeHelper


class TodoAPI:
    """
    待办事项 API 服务

    提供完整的 CRUD 操作和查询接口
    所有 API 返回统一格式：{'success': bool, 'data': Any, 'message': str}
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._storage = TodoStorage(data_dir)
        self._storage.load()

    def _success(self, data: Any = None, message: str = 'OK') -> dict:
        return {'success': True, 'data': data, 'message': message}

    def _error(self, message: str, code: int = 400) -> dict:
        return {'success': False, 'error': message, 'code': code, 'data': None, 'message': message}

    # ========== Todo CRUD ==========

    def list_todos(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> dict:
        """
        获取待办列表

        GET /api/todos
        参数：
            status: 状态过滤 (pending/in-progress/completed/archived/cancelled)
            priority: 优先级过滤 (urgent-important/important/urgent/normal)
            category: 分类 ID 过滤
            search: 搜索关键词
        """
        # 解析状态
        status_enum = None
        if status:
            try:
                status_enum = TodoStatus(status)
            except ValueError:
                return self._error(f'无效的状态值: {status}')

        # 解析优先级
        priority_enum = None
        if priority:
            try:
                priority_enum = Priority(priority)
            except ValueError:
                return self._error(f'无效的优先级值: {priority}')

        if search:
            todos = self._storage.search_todos(search)
        else:
            todos = self._storage.get_all_todos(
                status=status_enum,
                priority=priority_enum,
                category=category,
            )

        return self._success({
            'items': [t.to_dict() for t in todos],
            'total': len(todos),
        })

    def get_todo(self, todo_id: str) -> dict:
        """
        获取单个待办详情

        GET /api/todos/:id
        """
        todo = self._storage.get_todo_by_id(todo_id)
        if not todo:
            return self._error('待办不存在', 404)
        return self._success(todo.to_dict())

    def create_todo(
        self,
        title: str,
        priority: str = 'normal',
        category: str = 'default',
        description: Optional[str] = None,
        deadline: Optional[str] = None,
        tags: Optional[list] = None,
        related_plan_id: Optional[str] = None,
        time_estimate: Optional[int] = None,
    ) -> dict:
        """
        创建新的待办事项

        POST /api/todos
        参数：
            title: 任务标题（必填）
            priority: 优先级 (urgent-important/important/urgent/normal)
            category: 分类 ID
            description: 详细描述
            deadline: 截止日期 (ISO 8601)
            tags: 标签列表
            related_plan_id: 关联 plan-helper 计划 ID
            time_estimate: 预估时间（分钟）
        """
        if not title or not title.strip():
            return self._error('标题不能为空')

        # 解析优先级
        try:
            priority_enum = Priority(priority)
        except ValueError:
            return self._error(f'无效的优先级: {priority}')

        # 验证分类是否存在
        cat = self._storage.get_category_by_id(category)
        if not cat:
            return self._error(f'分类不存在: {category}')

        # 验证日期格式
        if deadline:
            dt = TimeHelper.parse_iso(deadline)
            if not dt:
                return self._error('无效的日期格式，请使用 ISO 8601 格式')

        todo = self._storage.create_todo(
            title=title.strip(),
            priority=priority_enum,
            category=category,
            description=description,
            deadline=deadline,
            tags=tags or [],
            related_plan_id=related_plan_id,
            time_estimate=time_estimate,
        )

        return self._success(todo.to_dict(), '待办创建成功')

    def update_todo(self, todo_id: str, **kwargs) -> dict:
        """
        更新待办事项

        PUT /api/todos/:id
        """
        # 验证字段
        if 'priority' in kwargs:
            try:
                kwargs['priority'] = Priority(kwargs['priority'])
            except ValueError:
                return self._error(f'无效的优先级: {kwargs["priority"]}')

        if 'status' in kwargs:
            try:
                kwargs['status'] = TodoStatus(kwargs['status'])
            except ValueError:
                return self._error(f'无效的状态: {kwargs["status"]}')

        todo = self._storage.update_todo(todo_id, **kwargs)
        if not todo:
            return self._error('待办不存在', 404)

        return self._success(todo.to_dict(), '待办更新成功')

    def delete_todo(self, todo_id: str) -> dict:
        """
        删除待办事项（归档）

        DELETE /api/todos/:id
        """
        success = self._storage.delete_todo(todo_id)
        if not success:
            return self._error('待办不存在', 404)
        return self._success(message='待办已归档')

    def complete_todo(self, todo_id: str, time_spent: Optional[int] = None) -> dict:
        """
        标记待办完成

        POST /api/todos/:id/complete
        """
        todo = self._storage.complete_todo(todo_id, time_spent)
        if not todo:
            return self._error('待办不存在', 404)
        return self._success(todo.to_dict(), '待办已完成')

    def cancel_todo(self, todo_id: str) -> dict:
        """
        标记待办取消

        POST /api/todos/:id/cancel
        """
        todo = self._storage.cancel_todo(todo_id)
        if not todo:
            return self._error('待办不存在', 404)
        return self._success(todo.to_dict(), '待办已取消')

    # ========== 子任务操作 ==========

    def add_subtask(self, todo_id: str, title: str) -> dict:
        """
        添加子任务

        POST /api/todos/:id/subtasks
        """
        if not title or not title.strip():
            return self._error('子任务标题不能为空')

        subtask = self._storage.add_subtask(todo_id, title.strip())
        if not subtask:
            return self._error('待办不存在', 404)

        return self._success(subtask.to_dict(), '子任务添加成功')

    def toggle_subtask(self, todo_id: str, subtask_id: str) -> dict:
        """
        切换子任务完成状态

        POST /api/todos/:id/subtasks/:subtaskId/toggle
        """
        success = self._storage.toggle_subtask(todo_id, subtask_id)
        if not success:
            return self._error('待办或子任务不存在', 404)

        todo = self._storage.get_todo_by_id(todo_id)
        return self._success(todo.to_dict() if todo else None, '子任务状态已更新')

    def delete_subtask(self, todo_id: str, subtask_id: str) -> dict:
        """
        删除子任务

        DELETE /api/todos/:id/subtasks/:subtaskId
        """
        success = self._storage.delete_subtask(todo_id, subtask_id)
        if not success:
            return self._error('待办或子任务不存在', 404)
        return self._success(message='子任务已删除')

    # ========== 分类操作 ==========

    def list_categories(self) -> dict:
        """
        获取所有分类

        GET /api/categories
        """
        categories = self._storage.get_categories()
        return self._success([c.to_dict() for c in categories])

    def create_category(
        self,
        name: str,
        color: str = '#6366f1',
        icon: str = 'circle',
        description: Optional[str] = None,
    ) -> dict:
        """
        创建新分类

        POST /api/categories
        """
        if not name or not name.strip():
            return self._error('分类名称不能为空')

        category = self._storage.create_category(
            name=name.strip(),
            color=color,
            icon=icon,
            description=description,
        )
        return self._success(category.to_dict(), '分类创建成功')

    def update_category(self, category_id: str, **kwargs) -> dict:
        """
        更新分类

        PUT /api/categories/:id
        """
        category = self._storage.update_category(category_id, **kwargs)
        if not category:
            return self._error('分类不存在', 404)
        return self._success(category.to_dict(), '分类更新成功')

    def delete_category(self, category_id: str) -> dict:
        """
        删除分类

        DELETE /api/categories/:id
        """
        success = self._storage.delete_category(category_id)
        if not success:
            return self._error('分类不存在', 404)
        return self._success(message='分类已删除，相关待办已移至默认分类')

    # ========== 查询与统计 ==========

    def get_stats(self) -> dict:
        """
        获取统计信息

        GET /api/todos/stats
        """
        stats = self._storage.get_stats()
        return self._success(stats)

    def get_overdue(self) -> dict:
        """
        获取逾期待办

        GET /api/todos/overdue
        """
        todos = self._storage.get_overdue_todos()
        return self._success([t.to_dict() for t in todos])

    def get_today(self) -> dict:
        """
        获取今日待办

        GET /api/todos/today
        """
        todos = self._storage.get_today_todos()
        return self._success([t.to_dict() for t in todos])

    # ========== 批量操作 ==========

    def batch_action(self, action: str, ids: list) -> dict:
        """
        批量操作

        POST /api/todos/batch
        参数：
            action: complete/cancel/archive/delete
            ids: 待办 ID 列表
        """
        if not ids:
            return self._error('ID 列表不能为空')

        valid_actions = {'complete', 'cancel', 'archive', 'delete'}
        if action not in valid_actions:
            return self._error(f'无效的操作: {action}，可选: {", ".join(valid_actions)}')

        results = {'success': 0, 'failed': 0, 'errors': []}

        for todo_id in ids:
            if action == 'complete':
                r = self._storage.complete_todo(todo_id)
            elif action == 'cancel':
                r = self._storage.cancel_todo(todo_id)
            elif action == 'archive':
                r = self._storage.delete_todo(todo_id)  # archive = soft delete
            elif action == 'delete':
                r = self._storage.delete_todo(todo_id)
            else:
                r = None

            if r:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f'{todo_id} 不存在')

        msg = f'操作完成: {results["success"]} 成功, {results["failed"]} 失败'
        return self._success(results, msg)

    # ========== 跨模块接口 ==========

    def get_todos_by_plan(self, plan_id: str) -> dict:
        """
        获取关联到指定计划的所有待办

        GET /api/integration/plans/:planId/todos
        """
        if not self._storage._loaded:
            self._storage.load()

        todos = [t for t in self._storage._todos if t.related_plan_id == plan_id]
        return self._success({
            'items': [t.to_dict() for t in todos],
            'total': len(todos),
            'plan_id': plan_id,
        })

    def create_todo_for_plan(
        self,
        plan_id: str,
        title: str,
        **kwargs,
    ) -> dict:
        """
        为指定计划创建关联待办

        POST /api/integration/plans/:planId/todos
        """
        return self.create_todo(
            title=title,
            related_plan_id=plan_id,
            **kwargs,
        )

    def track_time(self, todo_id: str, duration: int) -> dict:
        """
        记录时间到指定待办（与 time-helper 联动）

        POST /api/integration/time-tracking
        参数：
            todo_id: 待办 ID
            duration: 时间（分钟）
        """
        todo = self._storage.get_todo_by_id(todo_id)
        if not todo:
            return self._error('待办不存在', 404)

        current_spent = todo.time_spent or 0
        self._storage.update_todo(todo_id, time_spent=current_spent + duration)

        todo = self._storage.get_todo_by_id(todo_id)
        return self._success(todo.to_dict(), '时间已记录')

    # ========== v0.3.0 新增接口 ==========

    def toggle_pin(self, todo_id: str) -> dict:
        """
        切换待办置顶状态

        POST /api/todos/:id/pin
        """
        todo = self._storage.get_todo_by_id(todo_id)
        if not todo:
            return self._error('待办不存在', 404)

        todo.toggle_pin()
        self._storage._save_todos()
        return self._success(todo.to_dict(), '已置顶' if todo.pinned else '已取消置顶')

    def reorder(self, ids: list) -> dict:
        """
        重新排序待办

        PUT /api/todos/reorder
        参数：
            ids: 按新顺序排列的待办 ID 列表
        """
        for i, todo_id in enumerate(ids):
            todo = self._storage.get_todo_by_id(todo_id)
            if todo:
                self._storage.update_todo(todo_id, sort_order=i)
        return self._success(message='排序已更新')

    def get_warning_todos(self) -> dict:
        """
        获取即将到期的待办（在 deadline_warning_days 天内）

        GET /api/todos/warning
        """
        if not self._storage._loaded:
            self._storage.load()

        todos = [t for t in self._storage._todos if t.needs_warning()]
        return self._success([t.to_dict() for t in todos])

    def export_data(self, format: str = 'json') -> dict:
        """
        导出数据

        GET /api/export?format=json|csv
        """
        from .export import TodoExporter
        exporter = TodoExporter(self._storage)

        if format == 'csv':
            data = exporter.export_csv()
        else:
            data = exporter.export_json()

        return self._success({'format': format, 'data': data})

    def import_data(self, data: str, format: str = 'json', merge: bool = True) -> dict:
        """
        导入数据

        POST /api/import
        参数：
            data: JSON 或 CSV 数据
            format: json|csv
            merge: True=合并, False=替换
        """
        from .export import TodoImporter
        importer = TodoImporter(self._storage)

        if format == 'csv':
            # CSV 需要从文件导入，这里只支持 JSON 字符串导入
            return self._error('CSV 导入需要文件路径')

        result = importer.import_json(data, merge=merge)
        if result['success']:
            return self._success(result, result['message'])
        return self._error(result['message'])

    def create_backup(self) -> dict:
        """
        创建数据备份

        POST /api/backup
        """
        from .export import AutoBackup
        backup = AutoBackup(self._storage)
        filepath = backup.run_backup()
        return self._success({'path': filepath}, '备份创建成功')

    def list_backups(self) -> dict:
        """
        获取备份列表

        GET /api/backups
        """
        from .export import AutoBackup
        backup = AutoBackup(self._storage)
        backups = backup.get_backup_list()
        return self._success(backups)

    def restore_backup(self, filepath: str) -> dict:
        """
        从备份恢复数据

        POST /api/backup/restore
        """
        from .export import AutoBackup
        backup = AutoBackup(self._storage)
        result = backup.restore_backup(filepath)
        if result['success']:
            return self._success(result, result['message'])
        return self._error(result['message'])
