"""
to-dos 数据导入/导出工具
支持 JSON 和 CSV 格式
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .types import Todo, Category, TodoStatus, Priority, RecurrenceType
from .storage import TodoStorage


class TodoExporter:
    """数据导出器"""

    def __init__(self, storage: TodoStorage):
        self.storage = storage

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        导出为 JSON 格式

        Args:
            filepath: 导出路径，为 None 时返回 JSON 字符串
        """
        data = {
            'version': '0.3.0',
            'exported_at': datetime.now().isoformat(),
            'todos': [t.to_dict() for t in self.storage._todos],
            'categories': [c.to_dict() for c in self.storage._categories],
        }

        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def export_csv(self, filepath: Optional[str] = None) -> str:
        """
        导出为 CSV 格式

        Args:
            filepath: 导出路径，为 None 时返回 CSV 字符串
        """
        headers = [
            'ID', '标题', '描述', '状态', '优先级', '分类',
            '截止日期', '标签', '子任务数', '预估时间(分钟)',
            '实际时间(分钟)', '创建时间', '更新时间',
        ]

        rows = []
        for t in self.storage._todos:
            rows.append([
                t.id,
                t.title,
                t.description or '',
                t.status.value if isinstance(t.status, TodoStatus) else t.status,
                t.priority.value if isinstance(t.priority, Priority) else t.priority,
                t.category,
                t.deadline or '',
                '; '.join(t.tags),
                len(t.subtasks),
                t.time_estimate or '',
                t.time_spent or '',
                t.created_at[:19],
                t.updated_at[:19],
            ])

        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        csv_str = output.getvalue()

        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_str)

        return csv_str

    def export_backup(self, backup_dir: Optional[str] = None) -> str:
        """
        创建自动备份

        Returns:
            备份文件路径
        """
        if backup_dir is None:
            backup_dir = self.storage.data_dir / 'backups'
        else:
            backup_dir = Path(backup_dir)

        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = backup_dir / f'todos_backup_{timestamp}.json'

        self.export_json(str(filepath))
        return str(filepath)


class TodoImporter:
    """数据导入器"""

    def __init__(self, storage: TodoStorage):
        self.storage = storage

    def import_json(self, filepath_or_data: str, merge: bool = True) -> Dict[str, Any]:
        """
        从 JSON 导入数据

        Args:
            filepath_or_data: JSON 文件路径或 JSON 字符串
            merge: True=合并, False=替换

        Returns:
            {'success': bool, 'message': str, 'count': int}
        """
        try:
            # 判断是文件路径还是 JSON 字符串
            if os.path.isfile(filepath_or_data):
                with open(filepath_or_data, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = json.loads(filepath_or_data)
        except (json.JSONDecodeError, IOError, OSError):
            return {'success': False, 'message': '无效的 JSON 数据', 'count': 0}

        if 'todos' not in data or not isinstance(data['todos'], list):
            return {'success': False, 'message': 'JSON 格式不正确：缺少 todos 字段', 'count': 0}

        count = 0

        if not merge:
            # 替换模式：清空现有数据
            self.storage._todos = []

        # 导入待办
        existing_ids = {t.id for t in self.storage._todos}
        for item in data['todos']:
            try:
                todo = Todo.from_dict(item)
                if merge and todo.id in existing_ids:
                    # 更新已有记录
                    idx = next(i for i, t in enumerate(self.storage._todos) if t.id == todo.id)
                    self.storage._todos[idx] = todo
                else:
                    self.storage._todos.append(todo)
                count += 1
            except Exception:
                continue

        # 导入分类
        if 'categories' in data and isinstance(data['categories'], list):
            existing_cat_ids = {c.id for c in self.storage._categories}
            for item in data['categories']:
                try:
                    cat = Category.from_dict(item)
                    if cat.id not in existing_cat_ids:
                        self.storage._categories.append(cat)
                except Exception:
                    continue

        self.storage._save_todos()
        self.storage._save_categories()

        return {
            'success': True,
            'message': f'导入成功: {count} 个待办',
            'count': count,
        }

    def import_csv(self, filepath: str, merge: bool = True) -> Dict[str, Any]:
        """
        从 CSV 导入数据（简化版）

        Returns:
            {'success': bool, 'message': str, 'count': int}
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0

                if not merge:
                    self.storage._todos = []

                for row in reader:
                    try:
                        from .utils import IdGenerator, TimeHelper
                        now = TimeHelper.now_iso()

                        # 解析优先级
                        priority = row.get('优先级', 'normal')
                        try:
                            priority_enum = Priority(priority)
                        except ValueError:
                            priority_enum = Priority.NORMAL

                        # 解析状态
                        status = row.get('状态', 'pending')
                        try:
                            status_enum = TodoStatus(status)
                        except ValueError:
                            status_enum = TodoStatus.PENDING

                        # 解析标签
                        tags_str = row.get('标签', '')
                        tags = [t.strip() for t in tags_str.split(';') if t.strip()]

                        todo = Todo(
                            id=row.get('ID', IdGenerator.generate_todo_id()),
                            title=row.get('标题', ''),
                            description=row.get('描述') or None,
                            created_at=row.get('创建时间', now),
                            updated_at=now,
                            deadline=row.get('截止日期') or None,
                            priority=priority_enum,
                            category=row.get('分类', 'default'),
                            status=status_enum,
                            tags=tags,
                        )

                        self.storage._todos.append(todo)
                        count += 1
                    except Exception:
                        continue

                self.storage._save_todos()
                return {
                    'success': True,
                    'message': f'导入成功: {count} 个待办',
                    'count': count,
                }
        except (IOError, OSError) as e:
            return {'success': False, 'message': f'读取文件失败: {e}', 'count': 0}


class AutoBackup:
    """自动备份机制"""

    def __init__(self, storage: TodoStorage, max_backups: int = 10):
        self.storage = storage
        self.exporter = TodoExporter(storage)
        self.max_backups = max_backups

    def run_backup(self) -> str:
        """执行备份并清理旧备份"""
        filepath = self.exporter.export_backup()

        # 清理旧备份
        self._cleanup_old_backups()

        return filepath

    def _cleanup_old_backups(self):
        """清理超出数量限制的旧备份"""
        backup_dir = self.storage.data_dir / 'backups'
        if not backup_dir.exists():
            return

        backups = sorted(
            backup_dir.glob('todos_backup_*.json'),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
            except OSError:
                pass

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """获取备份列表"""
        backup_dir = self.storage.data_dir / 'backups'
        if not backup_dir.exists():
            return []

        backups = sorted(
            backup_dir.glob('todos_backup_*.json'),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        return [
            {
                'path': str(b),
                'filename': b.name,
                'size': b.stat().st_size,
                'created': datetime.fromtimestamp(b.stat().st_mtime).isoformat(),
            }
            for b in backups
        ]

    def restore_backup(self, filepath: str) -> Dict[str, Any]:
        """从备份恢复"""
        importer = TodoImporter(self.storage)
        return importer.import_json(filepath, merge=False)
