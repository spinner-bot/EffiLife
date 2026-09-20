"""
API 网关核心

统一入口，路由请求到各模块 API，并提供跨模块聚合查询。
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class APIGateway:
    """
    统一 API 网关

    使用方式:
        gateway = APIGateway.get_instance()
        gateway.register_module('plan-helper', plan_api)
        gateway.register_module('to-dos', todo_api)
        gateway.register_module('time-helper', time_api)

        # 调用模块 API
        result = gateway.call('to-dos', 'list_todos', status='pending')

        # 跨模块查询
        result = gateway.query_plan_with_todos(plan_id='1')
    """

    _instance = None

    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._routes: Dict[str, callable] = {}

    @classmethod
    def get_instance(cls) -> 'APIGateway':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    # ========== 模块注册 ==========

    def register_module(self, name: str, api_instance: Any):
        """
        注册模块 API

        Args:
            name: 模块名 ('plan-helper', 'to-dos', 'time-helper')
            api_instance: 模块的 API 实例
        """
        self._modules[name] = api_instance

    def unregister_module(self, name: str):
        """注销模块"""
        self._modules.pop(name, None)

    def get_module(self, name: str) -> Optional[Any]:
        """获取模块 API 实例"""
        return self._modules.get(name)

    def list_modules(self) -> List[str]:
        """列出已注册模块"""
        return list(self._modules.keys())

    # ========== 路由注册 ==========

    def register_route(self, path: str, handler: callable):
        """注册自定义路由"""
        self._routes[path] = handler

    # ========== 统一调用 ==========

    def call(self, module: str, method: str, **kwargs) -> dict:
        """
        调用模块 API 方法

        Args:
            module: 模块名
            method: 方法名
            **kwargs: 方法参数

        Returns:
            统一格式 {'success': bool, 'data': Any, 'message': str}
        """
        api = self._modules.get(module)
        if not api:
            return self._error(f'模块 {module} 未注册', 404)

        func = getattr(api, method, None)
        if not func:
            return self._error(f'模块 {module} 没有方法 {method}', 404)

        try:
            result = func(**kwargs)
            return result
        except Exception as e:
            return self._error(f'调用失败: {str(e)}', 500)

    def handle(self, path: str, method: str = 'GET', data: Optional[dict] = None) -> dict:
        """
        统一路由处理

        支持路径格式:
            /api/{module}/{method}
            /api/integration/{query_type}
        """
        # 先检查自定义路由
        if path in self._routes:
            try:
                return self._routes[path](method, data or {})
            except Exception as e:
                return self._error(f'路由处理失败: {str(e)}', 500)

        parts = [p for p in path.strip('/').split('/') if p]

        if len(parts) < 2:
            return self._error('无效路径', 400)

        # /api/integration/* - 跨模块查询
        if parts[0] == 'api' and parts[1] == 'integration':
            return self._handle_integration(parts[2:], method, data or {})

        # /api/{module}/{method}
        if parts[0] == 'api':
            module = parts[1]
            method_name = parts[2] if len(parts) > 2 else 'list'
            return self.call(module, method_name, **(data or {}))

        return self._error('未知路径', 404)

    # ========== 跨模块查询接口 ==========

    def _handle_integration(self, parts: List[str], method: str, data: dict) -> dict:
        """处理跨模块查询"""
        if not parts:
            return self._error('请指定查询类型', 400)

        query_type = parts[0]

        if query_type == 'plan-detail':
            plan_id = data.get('plan_id') or (parts[1] if len(parts) > 1 else None)
            return self.query_plan_full(plan_id)

        elif query_type == 'plan-todos':
            plan_id = data.get('plan_id') or (parts[1] if len(parts) > 1 else None)
            return self.query_plan_todos(plan_id)

        elif query_type == 'todo-time':
            todo_id = data.get('todo_id') or (parts[1] if len(parts) > 1 else None)
            return self.query_todo_time_records(todo_id)

        elif query_type == 'daily-summary':
            date = data.get('date') or (parts[1] if len(parts) > 1 else None)
            return self.query_daily_summary(date)

        elif query_type == 'user-dashboard':
            return self.query_user_dashboard()

        elif query_type == 'stats':
            return self.query_all_stats()

        else:
            return self._error(f'未知查询类型: {query_type}', 404)

    def query_plan_full(self, plan_id: str) -> dict:
        """
        查询计划完整信息

        包含计划详情 + 关联待办 + 关联时间记录
        """
        # 获取计划详情
        plan_result = self.call('plan-helper', 'get_plan', plan_id=plan_id)
        if not plan_result.get('success'):
            return self._error(f'计划不存在: {plan_id}', 404)

        # 获取关联待办
        todos_result = self.call('to-dos', 'get_todos_by_plan', plan_id=plan_id)
        todos = []
        if todos_result.get('success'):
            todos_data = todos_result.get('data', {})
            todos = todos_data.get('items', []) if isinstance(todos_data, dict) else []

        # 组装结果
        plan_data = plan_result.get('data', {})
        return self._success({
            'plan': plan_data,
            'todos': todos,
            'todos_count': len(todos),
            'todos_completed': sum(1 for t in todos if t.get('status') == 'completed'),
        })

    def query_plan_todos(self, plan_id: str) -> dict:
        """查询计划关联的所有待办"""
        result = self.call('to-dos', 'get_todos_by_plan', plan_id=plan_id)
        if not result.get('success'):
            return self._error('查询失败', 500)

        todos_data = result.get('data', {})
        todos = todos_data.get('items', []) if isinstance(todos_data, dict) else []

        # 统计
        total = len(todos)
        completed = sum(1 for t in todos if t.get('status') == 'completed')
        pending = sum(1 for t in todos if t.get('status') == 'pending')
        in_progress = sum(1 for t in todos if t.get('status') == 'in-progress')

        return self._success({
            'plan_id': plan_id,
            'items': todos,
            'total': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'completion_rate': round(completed / total * 100, 1) if total > 0 else 0,
        })

    def query_todo_time_records(self, todo_id: str) -> dict:
        """查询待办关联的时间记录"""
        # 先获取待办详情
        todo_result = self.call('to-dos', 'get_todo', todo_id=todo_id)
        if not todo_result.get('success'):
            return self._error(f'待办不存在: {todo_id}', 404)

        todo_data = todo_result.get('data', {})
        time_spent = todo_data.get('time_spent')
        time_estimate = todo_data.get('time_estimate')

        return self._success({
            'todo_id': todo_id,
            'todo_title': todo_data.get('title', ''),
            'time_spent': time_spent,
            'time_estimate': time_estimate,
            'progress': round((time_spent or 0) / time_estimate * 100, 1) if time_estimate else None,
        })

    def query_daily_summary(self, date_str: Optional[str] = None) -> dict:
        """
        查询每日总结

        聚合三个模块的当日数据。
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        summary = {
            'date': date_str,
            'modules': {},
        }

        # 时间记录
        time_api = self._modules.get('time-helper')
        if time_api:
            try:
                # time-helper 的 DataCore 方法
                records = time_api.load_records(date_str)
                stat_result = time_api.calc_real_time_stat(date_str)
                stat, prog, bg_tag, target, plan_exists, plan_name, plan_type, total_used, has_records, _ = stat_result
                summary['modules']['time-helper'] = {
                    'records_count': len(records),
                    'total_hours': round(total_used, 1),
                    'plan_name': plan_name,
                    'progress': prog,
                    'stat': {k: round(v, 2) for k, v in stat.items()},
                    'target': target,
                }
            except Exception as e:
                summary['modules']['time-helper'] = {'error': str(e)}

        # 待办
        todo_api = self._modules.get('to-dos')
        if todo_api:
            try:
                today_result = todo_api.get_today()
                overdue_result = todo_api.get_overdue()
                stats_result = todo_api.get_stats()

                today_items = today_result.get('data', [])
                if isinstance(today_items, dict):
                    today_items = today_items.get('items', [])

                summary['modules']['to-dos'] = {
                    'today_count': len(today_items),
                    'today_items': [t.get('title', '') for t in today_items[:10]],
                    'overdue_count': len(overdue_result.get('data', [])),
                    'stats': stats_result.get('data', {}),
                }
            except Exception as e:
                summary['modules']['to-dos'] = {'error': str(e)}

        # 计划
        plan_api = self._modules.get('plan-helper')
        if plan_api:
            try:
                plans_result = plan_api.list_plans()
                summary['modules']['plan-helper'] = {
                    'plans_count': plans_result.get('data', {}).get('count', 0),
                }
            except Exception as e:
                summary['modules']['plan-helper'] = {'error': str(e)}

        return self._success(summary)

    def query_user_dashboard(self) -> dict:
        """
        用户仪表盘

        聚合所有模块的概览数据。
        """
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'modules': {},
        }

        # 待办概览
        todo_api = self._modules.get('to-dos')
        if todo_api:
            try:
                stats = todo_api.get_stats()
                dashboard['modules']['to-dos'] = stats.get('data', {})
            except Exception:
                dashboard['modules']['to-dos'] = {}

        # 计划概览
        plan_api = self._modules.get('plan-helper')
        if plan_api:
            try:
                plans = plan_api.list_plans()
                dashboard['modules']['plan-helper'] = plans.get('data', {})
            except Exception:
                dashboard['modules']['plan-helper'] = {}

        # 时间概览
        time_api = self._modules.get('time-helper')
        if time_api:
            try:
                stat_result = time_api.calc_real_time_stat()
                stat, prog, bg_tag, target, plan_exists, plan_name, _, total_used, _, _, _ = stat_result
                dashboard['modules']['time-helper'] = {
                    'progress': prog,
                    'total_hours': round(total_used, 1),
                    'plan_name': plan_name,
                }
            except Exception:
                dashboard['modules']['time-helper'] = {}

        return self._success(dashboard)

    def query_all_stats(self) -> dict:
        """获取所有模块的统计"""
        stats = {}

        for module_name, api in self._modules.items():
            try:
                if hasattr(api, 'get_stats'):
                    result = api.get_stats()
                    stats[module_name] = result.get('data', result)
                else:
                    stats[module_name] = {'status': 'registered', 'message': '无统计接口'}
            except Exception as e:
                stats[module_name] = {'error': str(e)}

        return self._success(stats)

    # ========== 辅助方法 ==========

    @staticmethod
    def _success(data: Any = None, message: str = 'OK') -> dict:
        return {'success': True, 'data': data, 'message': message}

    @staticmethod
    def _error(message: str, code: int = 400) -> dict:
        return {'success': False, 'error': message, 'code': code, 'data': None, 'message': message}
