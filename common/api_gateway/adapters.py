"""
模块适配器

将各模块的 API 输出适配为统一格式，便于跨模块数据交换。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from ..schemas.models import UnifiedPlan, UnifiedTodo, UnifiedTimeRecord


class PlanAdapter:
    """plan-helper 适配器"""

    @staticmethod
    def to_unified_plan(plan_data: dict) -> UnifiedPlan:
        """将 plan-helper 的 API 输出转换为 UnifiedPlan"""
        return UnifiedPlan(
            id=str(plan_data.get('id', '')),
            name=plan_data.get('name', ''),
            module='plan-helper',
            plan_type='standard',
            date='-'.join(str(d) for d in plan_data.get('date', [])) if plan_data.get('date') else None,
            sections=plan_data.get('sections', []),
            total_tasks=plan_data.get('total_tasks', 0),
            completed_tasks=plan_data.get('completed_tasks', 0),
            progress_percentage=plan_data.get('progress_percentage', 0.0),
            estimated_minutes=plan_data.get('estimated_minutes', 0.0),
        )

    @staticmethod
    def to_unified_plan_from_summary(summary: dict) -> UnifiedPlan:
        """从 list_plans 的 summary 数据创建 UnifiedPlan"""
        return UnifiedPlan(
            id=str(summary.get('id', '')),
            name=summary.get('name', ''),
            module='plan-helper',
            plan_type='standard',
            date='-'.join(str(d) for d in summary.get('date', [])) if summary.get('date') else None,
            total_tasks=summary.get('total_tasks', 0),
            completed_tasks=summary.get('completed_tasks', 0),
            progress_percentage=summary.get('progress_percentage', 0.0),
            estimated_minutes=summary.get('estimated_minutes', 0.0),
        )

    @staticmethod
    def extract_task_ids(plan_data: dict) -> List[str]:
        """提取计划中所有任务 ID"""
        task_ids = []
        for section in plan_data.get('sections', []):
            for task in section.get('tasks', []):
                task_id = task.get('content', '')
                if task_id:
                    task_ids.append(f"{section.get('letter', '')}{task.get('index', '')}")
        return task_ids


class TodoAdapter:
    """to-dos 适配器"""

    @staticmethod
    def to_unified_todo(todo_data: dict) -> UnifiedTodo:
        """将 to-dos 的 API 输出转换为 UnifiedTodo"""
        return UnifiedTodo(
            id=todo_data.get('id', ''),
            title=todo_data.get('title', ''),
            created_at=todo_data.get('created_at', ''),
            updated_at=todo_data.get('updated_at', ''),
            priority=todo_data.get('priority', 'normal'),
            category=todo_data.get('category', 'default'),
            status=todo_data.get('status', 'pending'),
            description=todo_data.get('description'),
            deadline=todo_data.get('deadline'),
            completed_at=todo_data.get('completed_at'),
            tags=todo_data.get('tags', []),
            subtasks=todo_data.get('subtasks', []),
            related_plan_id=todo_data.get('related_plan_id'),
            time_estimate=todo_data.get('time_estimate'),
            time_spent=todo_data.get('time_spent'),
            notes=todo_data.get('notes'),
            recurrence=todo_data.get('recurrence', 'none'),
            deadline_warning_days=todo_data.get('deadline_warning_days', 3),
            sort_order=todo_data.get('sort_order', 0),
            pinned=todo_data.get('pinned', False),
        )

    @staticmethod
    def from_unified_todo(unified: UnifiedTodo) -> dict:
        """将 UnifiedTodo 转换为 to-dos 的创建参数"""
        return {
            'title': unified.title,
            'priority': unified.priority,
            'category': unified.category,
            'description': unified.description,
            'deadline': unified.deadline,
            'tags': unified.tags,
            'related_plan_id': unified.related_plan_id,
            'time_estimate': unified.time_estimate,
        }


class TimeAdapter:
    """time-helper 适配器"""

    @staticmethod
    def to_unified_record(record: dict, record_id: str = '') -> UnifiedTimeRecord:
        """将 time-helper 的 record 转换为 UnifiedTimeRecord"""
        # 计算时长
        start = record.get('开始', '00:00')
        end = record.get('结束', '00:00')
        try:
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            duration = (eh * 60 + em - sh * 60 - sm) / 60
            if duration < 0:
                duration += 24
        except (ValueError, TypeError):
            duration = record.get('时长', 0)

        return UnifiedTimeRecord(
            id=record_id or f"TR-{record.get('日期', '')}-{start.replace(':', '')}",
            date=record.get('日期', ''),
            start_time=start,
            end_time=end,
            duration_hours=round(duration, 2),
            content=record.get('内容', ''),
            tag=record.get('标签', ''),
            related_todo_id=record.get('related_todo_id'),
            related_plan_id=record.get('related_plan_id'),
        )

    @staticmethod
    def from_unified_record(unified: UnifiedTimeRecord) -> dict:
        """将 UnifiedTimeRecord 转换为 time-helper 的 record 格式"""
        return {
            '日期': unified.date,
            '开始': unified.start_time,
            '结束': unified.end_time,
            '时长': unified.duration_hours,
            '内容': unified.content,
            '标签': unified.tag,
            'related_todo_id': unified.related_todo_id,
            'related_plan_id': unified.related_plan_id,
        }
