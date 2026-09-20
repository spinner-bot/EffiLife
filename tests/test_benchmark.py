"""
EffiLife 性能基准测试

测量跨模块操作的性能，确保集成层不会引入显著延迟。
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'to-dos'))

from src.api import TodoAPI
from common.bootstrap import EffiLifeIntegration, reset_integration
from common.data_manager import DataManager
from common.event_bus import EventBus, EventType


class BenchmarkResult:
    """基准测试结果"""
    def __init__(self, name: str, iterations: int, total_time: float):
        self.name = name
        self.iterations = iterations
        self.total_time = total_time
        self.avg_time = total_time / iterations if iterations > 0 else 0
        self.ops_per_second = iterations / total_time if total_time > 0 else 0

    def __str__(self):
        return (f'{self.name}: {self.iterations} ops in {self.total_time:.3f}s '
                f'(avg {self.avg_time * 1000:.2f}ms/op, '
                f'{self.ops_per_second:.0f} ops/sec)')


def benchmark_todo_crud(iterations=100) -> BenchmarkResult:
    """基准测试 1: Todo CRUD 操作"""
    test_dir = tempfile.mkdtemp(prefix='effilife_bench_')
    try:
        api = TodoAPI(data_dir=test_dir)

        start = time.perf_counter()
        for i in range(iterations):
            # 创建
            r = api.create_todo(title=f'Benchmark todo {i}', priority='normal')
            todo_id = r['data']['id']
            # 读取
            api.get_todo(todo_id)
            # 更新
            api.update_todo(todo_id, description=f'Updated {i}')
            # 完成
            api.complete_todo(todo_id, time_spent=i % 60)
        elapsed = time.perf_counter() - start

        return BenchmarkResult('Todo CRUD (create+read+update+complete)', iterations, elapsed)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def benchmark_event_bus(iterations=1000) -> BenchmarkResult:
    """基准测试 2: 事件总线发布/订阅"""
    eb = EventBus()

    # 注册 5 个处理器
    handlers_called = [0]
    def handler(event):
        handlers_called[0] += 1

    for i in range(5):
        eb.subscribe('todo.created', handler)

    start = time.perf_counter()
    for i in range(iterations):
        eb.emit('todo.created', 'benchmark', {'index': i})
    elapsed = time.perf_counter() - start

    EventBus._instance = None
    return BenchmarkResult(f'EventBus emit ({iterations} events, 5 handlers)', iterations, elapsed)


def benchmark_data_manager_refs(iterations=500) -> BenchmarkResult:
    """基准测试 3: DataManager 跨模块引用"""
    test_dir = tempfile.mkdtemp(prefix='effilife_bench_')
    try:
        dm = DataManager(data_root=test_dir)
        dm.load()

        start = time.perf_counter()
        for i in range(iterations):
            dm.link_entities(
                source_module='to-dos',
                source_id=f'TODO-{i:04d}',
                target_module='plan-helper',
                target_id=f'PLAN-{i % 10:04d}',
                relation_type='belongs_to',
            )
        elapsed = time.perf_counter() - start

        DataManager.reset_instance()
        return BenchmarkResult('DataManager link_entities', iterations, elapsed)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def benchmark_gateway_query(iterations=200) -> BenchmarkResult:
    """基准测试 4: API 网关查询"""
    test_dir = tempfile.mkdtemp(prefix='effilife_bench_')
    try:
        integration = EffiLifeIntegration(data_root=test_dir)
        integration.initialize()

        todo_dir = os.path.join(test_dir, 'todos')
        todo_api = TodoAPI(data_dir=todo_dir)

        # 预填充数据
        for i in range(50):
            todo_api.create_todo(
                title=f'Pre-filled todo {i}',
                related_plan_id=f'PLAN-{i % 5}',
            )

        integration.register_todo_api(todo_api)

        start = time.perf_counter()
        for i in range(iterations):
            integration.gateway.query_plan_todos(f'PLAN-{i % 5}')
            integration.gateway.query_daily_summary()
        elapsed = time.perf_counter() - start

        reset_integration()
        return BenchmarkResult('Gateway cross-module query', iterations, elapsed)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def benchmark_auth_operations(iterations=100) -> BenchmarkResult:
    """基准测试 5: 身份认证操作"""
    test_dir = tempfile.mkdtemp(prefix='effilife_bench_')
    try:
        from common.auth import AuthManager
        auth = AuthManager(data_dir=test_dir)
        auth.load()

        start = time.perf_counter()
        for i in range(iterations):
            auth.register(f'user_{i}', f'pass_{i}', f'User {i}')
        elapsed = time.perf_counter() - start

        AuthManager.reset_instance()
        return BenchmarkResult('AuthManager register', iterations, elapsed)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def benchmark_integration_event_flow(iterations=100) -> BenchmarkResult:
    """基准测试 6: 集成事件流"""
    test_dir = tempfile.mkdtemp(prefix='effilife_bench_')
    try:
        integration = EffiLifeIntegration(data_root=test_dir)
        integration.initialize()

        todo_dir = os.path.join(test_dir, 'todos')
        todo_api = TodoAPI(data_dir=todo_dir)
        integration.register_todo_api(todo_api)

        start = time.perf_counter()
        for i in range(iterations):
            # 创建待办 -> 触发事件
            r = todo_api.create_todo(title=f'Flow todo {i}')
            todo_id = r['data']['id']
            # 完成待办 -> 触发事件
            todo_api.complete_todo(todo_id, time_spent=15)
        elapsed = time.perf_counter() - start

        reset_integration()
        return BenchmarkResult('Integration event flow (create+complete)', iterations, elapsed)
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def run_benchmarks():
    """运行所有基准测试"""
    print('=' * 60)
    print('  EffiLife Performance Benchmarks')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)

    benchmarks = [
        ('Todo CRUD', lambda: benchmark_todo_crud(100)),
        ('EventBus', lambda: benchmark_event_bus(1000)),
        ('DataManager refs', lambda: benchmark_data_manager_refs(500)),
        ('Gateway queries', lambda: benchmark_gateway_query(200)),
        ('Auth operations', lambda: benchmark_auth_operations(100)),
        ('Integration flow', lambda: benchmark_integration_event_flow(100)),
    ]

    results = []
    for name, func in benchmarks:
        try:
            r = func()
            results.append(r)
            print(f'  {r}')
        except Exception as e:
            print(f'  ERROR in {name}: {e}')
            import traceback
            traceback.print_exc()

    print(f'\n{"=" * 60}')
    print('  Performance Summary')
    print(f'{"=" * 60}')

    all_pass = True
    for r in results:
        status = 'PASS' if r.avg_time < 0.1 else 'WARN' if r.avg_time < 1.0 else 'FAIL'
        if status == 'FAIL':
            all_pass = False
        print(f'  [{status}] {r.name}: avg {r.avg_time * 1000:.2f}ms/op')

    print(f'\n  Threshold: < 100ms/op = PASS, < 1000ms/op = WARN, >= 1000ms/op = FAIL')
    print(f'{"=" * 60}')

    return all_pass


if __name__ == '__main__':
    success = run_benchmarks()
    sys.exit(0 if success else 1)
