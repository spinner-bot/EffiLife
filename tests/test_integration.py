"""
EffiLife 端到端集成测试

验证跨模块数据流和联动功能。
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 确保项目根目录在路径中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入 to-dos 模块
sys.path.insert(0, str(PROJECT_ROOT / 'to-dos'))
from src.api import TodoAPI
from src.types import Priority, TodoStatus

# 导入 common
from common.bootstrap import EffiLifeIntegration, reset_integration
from common.event_bus import EventBus, EventType
from common.data_manager import DataManager
from common.auth import AuthManager
from common.api_gateway import APIGateway
from common.schemas.models import UnifiedTodo, UnifiedPlan, UnifiedTimeRecord


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, name: str, passed: bool, detail: str = ''):
        if passed:
            self.passed += 1
            print(f'  PASS: {name}')
        else:
            self.failed += 1
            self.errors.append({'name': name, 'detail': detail})
            print(f'  FAIL: {name} - {detail}')

    def summary(self):
        total = self.passed + self.failed
        print(f'\n{"=" * 50}')
        print(f'  Integration Tests: {self.passed}/{total} passed')
        if self.errors:
            print(f'  Failed tests:')
            for e in self.errors:
                print(f'    - {e["name"]}: {e["detail"]}')
        print(f'{"=" * 50}')
        return self.failed == 0


def setup_test_env():
    """创建测试环境"""
    test_dir = tempfile.mkdtemp(prefix='effilife_test_')
    return test_dir


def cleanup_test_env(test_dir):
    """清理测试环境"""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)


def test_schemas():
    """测试 1: 统一数据模型"""
    print('\n--- Test Group: Schemas ---')
    result = TestResult()

    # 1.1 UnifiedTodo
    todo = UnifiedTodo(
        id='TODO-20260920-0001',
        title='测试待办',
        priority='important',
        status='pending',
    )
    d = todo.to_dict()
    result.record('UnifiedTodo.to_dict', 'id' in d and d['title'] == '测试待办')

    todo2 = UnifiedTodo.from_dict(d)
    result.record('UnifiedTodo.from_dict', todo2.id == todo.id and todo2.title == todo.title)

    # 1.2 UnifiedPlan
    plan = UnifiedPlan(
        id='1',
        name='测试计划',
        plan_type='standard',
    )
    d = plan.to_dict()
    result.record('UnifiedPlan.to_dict', d['name'] == '测试计划')

    plan2 = UnifiedPlan.from_dict(d)
    result.record('UnifiedPlan.from_dict', plan2.id == '1')

    # 1.3 UnifiedTimeRecord
    record = UnifiedTimeRecord(
        id='TR-20260920-0800',
        date='2026-09-20',
        start_time='08:00',
        end_time='09:00',
        duration_hours=1.0,
        content='测试记录',
        tag='工作',
    )
    d = record.to_dict()
    result.record('UnifiedTimeRecord.to_dict', d['duration_hours'] == 1.0)

    record2 = UnifiedTimeRecord.from_dict(d)
    result.record('UnifiedTimeRecord.from_dict', record2.id == 'TR-20260920-0800')

    return result


def test_data_manager():
    """测试 2: 数据管理器"""
    print('\n--- Test Group: DataManager ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        dm = DataManager(data_root=test_dir)
        dm.load()

        # 2.1 添加引用
        ref = dm.link_entities(
            source_module='to-dos',
            source_id='TODO-001',
            target_module='plan-helper',
            target_id='PLAN-001',
            relation_type='belongs_to',
        )
        result.record('link_entities', ref.source_id == 'TODO-001')

        # 2.2 查询引用
        refs = dm.find_linked_ids('TODO-001', 'plan-helper')
        result.record('find_linked_ids', 'PLAN-001' in refs)

        # 2.3 反向查询
        refs = dm.get_references_by_target('PLAN-001')
        result.record('get_references_by_target', len(refs) > 0)

        # 2.4 按类型查询
        refs = dm.get_references_by_type('belongs_to')
        result.record('get_references_by_type', len(refs) > 0)

        # 2.5 删除引用
        removed = dm.remove_reference('TODO-001', 'PLAN-001')
        result.record('remove_reference', removed)

        refs = dm.find_linked_ids('TODO-001', 'plan-helper')
        result.record('reference_removed', len(refs) == 0)

        # 2.6 统计
        stats = dm.get_stats()
        result.record('get_stats', 'total_references' in stats)

    finally:
        DataManager.reset_instance()
        cleanup_test_env(test_dir)

    return result


def test_event_bus():
    """测试 3: 事件总线"""
    print('\n--- Test Group: EventBus ---')
    result = TestResult()

    eb = EventBus()

    received_events = []

    def handler(event):
        received_events.append(event)

    # 3.1 订阅和发布
    eb.subscribe('todo.completed', handler)
    eb.emit('todo.completed', 'to-dos', {'todo_id': 'T001'})
    result.record('subscribe and emit', len(received_events) == 1)

    # 3.2 事件数据
    result.record('event_data', received_events[0].data.get('todo_id') == 'T001')

    # 3.3 通配符
    wildcard_events = []
    def wildcard_handler(event):
        wildcard_events.append(event)

    eb.subscribe('*', wildcard_handler)
    eb.emit('plan.created', 'plan-helper', {'plan_id': 'P001'})
    result.record('wildcard_handler', len(wildcard_events) == 1)

    # 3.4 事件日志
    log = eb.get_event_log()
    result.record('event_log', len(log) == 2)

    # 3.5 按类型筛选
    filtered = eb.get_events_by_type('todo.completed')
    result.record('events_by_type', len(filtered) == 1)

    # 3.6 统计
    stats = eb.get_stats()
    result.record('event_stats', stats['total_events'] == 2)

    EventBus._instance = None
    return result


def test_auth_manager():
    """测试 4: 身份认证"""
    print('\n--- Test Group: AuthManager ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        auth = AuthManager(data_dir=test_dir)
        auth.load()

        # 4.1 注册
        reg = auth.register('testuser', 'pass1234', '测试用户')
        result.record('register', reg['success'] and reg['user'].username == 'testuser')

        # 4.2 重复注册
        reg2 = auth.register('testuser', 'pass5678')
        result.record('duplicate_register', not reg2['success'])

        # 4.3 登录
        login = auth.login('testuser', 'pass1234')
        result.record('login', login['success'] and login['user'].username == 'testuser')

        # 4.4 当前用户
        user = auth.get_current_user()
        result.record('get_current_user', user is not None and user.username == 'testuser')

        # 4.5 已登录
        result.record('is_logged_in', auth.is_logged_in())

        # 4.6 登出
        logout = auth.logout()
        result.record('logout', logout['success'])
        result.record('after_logout', not auth.is_logged_in())

        # 4.7 错误密码
        login2 = auth.login('testuser', 'wrongpass')
        result.record('wrong_password', not login2['success'])

        # 4.8 统计
        stats = auth.get_stats()
        result.record('auth_stats', stats['total_users'] == 1)

    finally:
        AuthManager.reset_instance()
        cleanup_test_env(test_dir)

    return result


def test_todo_api_basic():
    """测试 5: to-dos API 基础功能"""
    print('\n--- Test Group: TodoAPI Basic ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        api = TodoAPI(data_dir=test_dir)

        # 5.1 创建待办
        r = api.create_todo(title='测试待办1', priority='important')
        result.record('create_todo', r['success'] and r['data']['title'] == '测试待办1')
        todo_id = r['data']['id']

        # 5.2 获取待办
        r = api.get_todo(todo_id)
        result.record('get_todo', r['success'] and r['data']['id'] == todo_id)

        # 5.3 列表
        r = api.list_todos()
        result.record('list_todos', r['success'] and r['data']['total'] >= 1)

        # 5.4 更新
        r = api.update_todo(todo_id, description='更新描述')
        result.record('update_todo', r['success'] and r['data']['description'] == '更新描述')

        # 5.5 完成
        r = api.complete_todo(todo_id, time_spent=30)
        result.record('complete_todo', r['success'] and r['data']['status'] == 'completed')

        # 5.6 统计
        r = api.get_stats()
        result.record('todo_stats', r['success'] and r['data']['completed'] >= 1)

        # 5.7 关联计划
        r2 = api.create_todo(title='关联待办', related_plan_id='PLAN-001')
        result.record('create_todo_with_plan', r2['success'] and r2['data']['related_plan_id'] == 'PLAN-001')

        # 5.8 按计划查询
        r3 = api.get_todos_by_plan('PLAN-001')
        result.record('get_todos_by_plan', r3['success'] and r3['data']['total'] >= 1)

    finally:
        cleanup_test_env(test_dir)

    return result


def test_integration_flow():
    """测试 6: 完整集成流程"""
    print('\n--- Test Group: Integration Flow ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        # 初始化集成
        integration = EffiLifeIntegration(data_root=test_dir)
        integration.initialize()

        # 创建 to-dos API
        todo_dir = os.path.join(test_dir, 'todos_data')
        todo_api = TodoAPI(data_dir=todo_dir)

        # 注册到网关
        integration.register_todo_api(todo_api)

        # 6.1 网关调用
        r = integration.gateway.call('to-dos', 'create_todo', title='集成测试待办')
        result.record('gateway_call', r['success'])
        todo_id = r['data']['id']

        # 6.2 创建带计划关联的待办
        r = integration.gateway.call('to-dos', 'create_todo',
                                      title='计划关联待办',
                                      related_plan_id='P001')
        result.record('create_with_plan_ref', r['success'])

        # 6.3 跨模块查询
        r = integration.gateway.query_plan_todos('P001')
        result.record('query_plan_todos', r['success'] and r['data']['total'] >= 1)

        # 6.4 发布事件
        event = integration.emit_event(
            event_type=EventType.TODO_COMPLETED.value,
            source_module='to-dos',
            data={'todo_id': todo_id, 'time_spent': 25},
        )
        result.record('emit_event', event.type == EventType.TODO_COMPLETED.value)

        # 6.5 事件日志
        log = integration.event_bus.get_event_log()
        result.record('event_logged', len(log) >= 1)

        # 6.6 集成统计
        stats = integration.get_stats()
        result.record('integration_stats', 'to-dos' in stats['modules'])

        # 6.7 数据管理器统计
        dm_stats = integration.data_manager.get_stats()
        result.record('data_manager_stats', 'total_references' in dm_stats)

    finally:
        reset_integration()
        cleanup_test_env(test_dir)

    return result


def test_cross_module_references():
    """测试 7: 跨模块引用"""
    print('\n--- Test Group: Cross-Module References ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        dm = DataManager(data_root=test_dir)
        dm.load()

        # 7.1 创建 todo -> plan 引用
        ref1 = dm.link_entities('to-dos', 'TODO-001', 'plan-helper', 'PLAN-001', 'belongs_to')
        result.record('link_todo_to_plan', ref1.relation_type == 'belongs_to')

        # 7.2 创建 time -> todo 引用
        ref2 = dm.link_entities('time-helper', 'TR-001', 'to-dos', 'TODO-001', 'tracks')
        result.record('link_time_to_todo', ref2.relation_type == 'tracks')

        # 7.3 链式查询: plan -> todos
        todo_ids = dm.find_linked_ids('PLAN-001', 'to-dos')
        # 反向查找
        refs = dm.get_references_by_target('PLAN-001')
        result.record('find_plan_todos', len(refs) >= 1)

        # 7.4 链式查询: todo -> time records
        time_ids = []
        refs = dm.get_references_by_target('TODO-001')
        for r in refs:
            if r.source_module == 'time-helper':
                time_ids.append(r.source_id)
        result.record('find_todo_time_records', 'TR-001' in time_ids)

        # 7.5 按模块对统计
        stats = dm.get_stats()
        result.record('module_pair_stats',
                       'to-dos->plan-helper' in stats['by_module_pair'] or
                       len(stats['by_module_pair']) > 0)

    finally:
        DataManager.reset_instance()
        cleanup_test_env(test_dir)

    return result


def test_api_gateway():
    """测试 8: API 网关"""
    print('\n--- Test Group: API Gateway ---')
    test_dir = setup_test_env()
    result = TestResult()

    try:
        gw = APIGateway()
        todo_dir = os.path.join(test_dir, 'todos')
        todo_api = TodoAPI(data_dir=todo_dir)
        gw.register_module('to-dos', todo_api)

        # 8.1 注册模块
        result.record('register_module', 'to-dos' in gw.list_modules())

        # 8.2 调用方法
        r = gw.call('to-dos', 'create_todo', title='网关测试')
        result.record('gateway_call_method', r['success'])

        # 8.3 未注册模块
        r = gw.call('unknown-module', 'list')
        result.record('unknown_module', not r['success'])

        # 8.4 未注册方法
        r = gw.call('to-dos', 'nonexistent_method')
        result.record('unknown_method', not r['success'])

        # 8.5 每日总结
        r = gw.query_daily_summary()
        result.record('daily_summary', r['success'] and 'date' in r['data'])

        # 8.6 用户仪表盘
        r = gw.query_user_dashboard()
        result.record('user_dashboard', r['success'])

        # 8.7 全部统计
        r = gw.query_all_stats()
        result.record('all_stats', r['success'])

    finally:
        APIGateway.reset_instance()
        cleanup_test_env(test_dir)

    return result


def run_all_tests():
    """运行所有集成测试"""
    print('=' * 50)
    print('  EffiLife Integration Tests')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 50)

    all_results = []
    test_groups = [
        ('Schemas', test_schemas),
        ('DataManager', test_data_manager),
        ('EventBus', test_event_bus),
        ('AuthManager', test_auth_manager),
        ('TodoAPI Basic', test_todo_api_basic),
        ('Integration Flow', test_integration_flow),
        ('Cross-Module References', test_cross_module_references),
        ('API Gateway', test_api_gateway),
    ]

    for name, test_func in test_groups:
        try:
            r = test_func()
            all_results.append((name, r))
        except Exception as e:
            print(f'\n  ERROR in {name}: {e}')
            import traceback
            traceback.print_exc()
            r = TestResult()
            r.record(f'{name} (exception)', False, str(e))
            all_results.append((name, r))

    # 总结
    total_passed = sum(r.passed for _, r in all_results)
    total_failed = sum(r.failed for _, r in all_results)
    total = total_passed + total_failed

    print(f'\n{"=" * 50}')
    print(f'  TOTAL: {total_passed}/{total} passed')
    if total_failed > 0:
        print(f'  FAILED: {total_failed}')
        for name, r in all_results:
            if r.failed > 0:
                print(f'    {name}: {r.failed} failed')
                for e in r.errors:
                    print(f'      - {e["name"]}: {e["detail"]}')
    else:
        print('  All tests passed!')
    print(f'{"=" * 50}')

    return total_failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
