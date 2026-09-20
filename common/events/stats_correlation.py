"""
统计关联器

将 time-helper 的时间统计与 plan-helper 的计划进度、to-dos 的完成情况关联。
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from ..event_bus import Event, EventBus
from ..data_manager import DataManager
from ..api_gateway import APIGateway


class StatsCorrelator:
    """
    统计关联器

    提供跨模块的统计分析：
    - 按计划维度统计时间分配
    - 按待办维度统计时间花费
    - 综合效率报告
    """

    def __init__(self, gateway: Optional[APIGateway] = None, data_manager: Optional[DataManager] = None):
        self.gateway = gateway or APIGateway.get_instance()
        self.data_manager = data_manager or DataManager.get_instance()
        self.event_bus = EventBus.get_instance()

    def get_plan_time_stats(self, plan_id: str) -> dict:
        """
        获取计划的时间统计

        聚合该计划下所有待办的时间花费。
        """
        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return {'error': 'to-dos 模块未注册'}

        # 获取计划关联的待办
        result = todo_api.get_todos_by_plan(plan_id=str(plan_id))
        if not result.get('success'):
            return {'error': '查询失败'}

        todos_data = result.get('data', {})
        todos = todos_data.get('items', []) if isinstance(todos_data, dict) else []

        total_estimate = 0
        total_spent = 0
        completed_count = 0
        total_count = len(todos)

        todo_details = []
        for todo in todos:
            estimate = todo.get('time_estimate', 0) or 0
            spent = todo.get('time_spent', 0) or 0
            total_estimate += estimate
            total_spent += spent
            if todo.get('status') == 'completed':
                completed_count += 1

            todo_details.append({
                'id': todo.get('id'),
                'title': todo.get('title'),
                'status': todo.get('status'),
                'time_estimate': estimate,
                'time_spent': spent,
                'efficiency': round(spent / estimate * 100, 1) if estimate > 0 else None,
            })

        return {
            'plan_id': plan_id,
            'total_todos': total_count,
            'completed_todos': completed_count,
            'completion_rate': round(completed_count / total_count * 100, 1) if total_count > 0 else 0,
            'total_estimate_minutes': total_estimate,
            'total_spent_minutes': total_spent,
            'time_efficiency': round(total_spent / total_estimate * 100, 1) if total_estimate > 0 else None,
            'todo_details': todo_details,
        }

    def get_daily_correlation(self, date_str: Optional[str] = None) -> dict:
        """
        获取每日关联统计

        将当天（或指定日期）的时间记录与待办/计划关联。
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        time_api = self.gateway.get_module('time-helper')
        todo_api = self.gateway.get_module('to-dos')

        result = {
            'date': date_str,
            'time_records': [],
            'related_todos': [],
            'total_hours': 0,
            'by_category': {},
        }

        # 获取时间记录
        if time_api:
            try:
                records = time_api.load_records(date_str)
                total_hours = 0
                by_category = {}

                for r in records:
                    duration = r.get('时长', 0)
                    total_hours += duration
                    tag = r.get('标签', '未分类')
                    by_category[tag] = by_category.get(tag, 0) + duration

                    record_info = {
                        'start': r.get('开始'),
                        'end': r.get('结束'),
                        'duration': duration,
                        'content': r.get('内容'),
                        'tag': tag,
                        'related_todo_id': r.get('related_todo_id'),
                    }
                    result['time_records'].append(record_info)

                result['total_hours'] = round(total_hours, 2)
                result['by_category'] = {k: round(v, 2) for k, v in by_category.items()}
            except Exception as e:
                result['error'] = str(e)

        # 获取当天完成的待办
        if todo_api:
            try:
                all_todos_result = todo_api.list_todos(status='completed')
                if all_todos_result.get('success'):
                    items = all_todos_result.get('data', {}).get('items', [])
                    for todo in items:
                        completed_at = todo.get('completed_at', '')
                        if completed_at and completed_at[:10] == date_str:
                            result['related_todos'].append({
                                'id': todo.get('id'),
                                'title': todo.get('title'),
                                'time_spent': todo.get('time_spent'),
                                'category': todo.get('category'),
                            })
            except Exception:
                pass

        return result

    def get_efficiency_report(self, days: int = 7) -> dict:
        """
        获取效率报告

        综合统计最近 N 天的数据。
        """
        from datetime import timedelta

        report = {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'daily_summaries': [],
            'totals': {
                'total_hours': 0,
                'todos_completed': 0,
                'todos_created': 0,
            },
        }

        total_hours = 0
        total_todos_completed = 0

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily = self.get_daily_correlation(date)
            report['daily_summaries'].append({
                'date': date,
                'total_hours': daily.get('total_hours', 0),
                'records_count': len(daily.get('time_records', [])),
                'todos_completed': len(daily.get('related_todos', [])),
            })
            total_hours += daily.get('total_hours', 0)
            total_todos_completed += len(daily.get('related_todos', []))

        report['totals']['total_hours'] = round(total_hours, 2)
        report['totals']['todos_completed'] = total_todos_completed
        report['totals']['avg_daily_hours'] = round(total_hours / days, 2) if days > 0 else 0

        return report
