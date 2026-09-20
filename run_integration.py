"""
EffiLife 集成系统入口

启动集成系统，注册所有模块，提供统一命令行界面。

用法:
    python run_integration.py                   # 交互模式
    python run_integration.py stats             # 查看统计
    python run_integration.py dashboard         # 查看仪表盘
    python run_integration.py test              # 运行集成测试
    python run_integration.py benchmark         # 运行性能测试
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'to-dos'))


def main():
    from common.bootstrap import EffiLifeIntegration
    from common.event_bus import EventType

    # 初始化集成系统
    integration = EffiLifeIntegration()
    integration.initialize()

    # 注册 to-dos 模块
    try:
        from src.api import TodoAPI
        todo_api = TodoAPI()
        integration.register_todo_api(todo_api)
        print('  [OK] to-dos 模块已注册')
    except Exception as e:
        print(f'  [WARN] to-dos 模块注册失败: {e}')
        todo_api = None

    # 注册 plan-helper 模块
    try:
        sys.path.insert(0, str(PROJECT_ROOT / 'plan-helper'))
        from modules import api as plan_api_module

        class PlanAPIWrapper:
            """包装 plan-helper 的函数式 API 为对象式 API"""
            def get_plan(self, plan_id):
                return plan_api_module.get_plan(plan_id).to_dict()
            def list_plans(self):
                return plan_api_module.list_plans().to_dict()
            def create_plan(self, **kwargs):
                return plan_api_module.create_plan(**kwargs).to_dict()
            def get_progress(self, plan_id):
                return plan_api_module.get_progress(plan_id).to_dict()

        plan_api = PlanAPIWrapper()
        integration.register_plan_api(plan_api)
        print('  [OK] plan-helper 模块已注册')
    except Exception as e:
        print(f'  [WARN] plan-helper 模块注册失败: {e}')

    # 处理命令行参数
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'stats':
            _show_stats(integration)
        elif cmd == 'dashboard':
            _show_dashboard(integration)
        elif cmd == 'test':
            _run_tests()
        elif cmd == 'benchmark':
            _run_benchmarks()
        elif cmd == 'events':
            _show_events(integration)
        elif cmd == 'help':
            _show_help()
        else:
            print(f'  未知命令: {cmd}')
            _show_help()
    else:
        _interactive_loop(integration)


def _show_stats(integration):
    """显示统计"""
    stats = integration.get_stats()
    print('\n  ====== EffiLife 集成统计 ======')
    print(f'  已注册模块: {", ".join(stats["modules"]) or "无"}')
    print(f'  事件总数: {stats["event_bus"]["total_events"]}')
    print(f'  跨模块引用: {stats["data_manager"]["total_references"]}')
    print(f'  用户数: {stats["auth"]["total_users"]}')
    if stats['auth']['current_user']:
        print(f'  当前用户: {stats["auth"]["current_user"]["username"]}')


def _show_dashboard(integration):
    """显示仪表盘"""
    r = integration.gateway.query_user_dashboard()
    if r['success']:
        data = r['data']
        print('\n  ====== EffiLife 仪表盘 ======')
        print(f'  时间: {data["timestamp"][:19]}')
        for module, info in data.get('modules', {}).items():
            print(f'\n  [{module}]')
            if isinstance(info, dict):
                for k, v in info.items():
                    if not isinstance(v, (dict, list)):
                        print(f'    {k}: {v}')


def _show_events(integration):
    """显示最近事件"""
    events = integration.event_bus.get_event_log(20)
    print(f'\n  最近 {len(events)} 个事件:')
    for e in events:
        print(f'    [{e.timestamp[:19]}] {e.type} ({e.source_module})')


def _run_tests():
    """运行集成测试"""
    print('\n  运行集成测试...')
    from tests.test_integration import run_all_tests
    run_all_tests()


def _run_benchmarks():
    """运行性能基准"""
    print('\n  运行性能基准测试...')
    from tests.test_benchmark import run_benchmarks
    run_benchmarks()


def _interactive_loop(integration):
    """交互模式"""
    print('\n  EffiLife 集成系统 v1.0.0')
    print('  输入 help 查看命令, q 退出\n')

    while True:
        try:
            cmd = input('  effilife> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n  再见!')
            break

        if not cmd:
            continue
        elif cmd in ('q', 'quit', 'exit'):
            print('  再见!')
            break
        elif cmd == 'help':
            _show_help()
        elif cmd == 'stats':
            _show_stats(integration)
        elif cmd == 'dashboard':
            _show_dashboard(integration)
        elif cmd == 'events':
            _show_events(integration)
        elif cmd == 'test':
            _run_tests()
        elif cmd == 'benchmark':
            _run_benchmarks()
        else:
            print(f'  未知命令: {cmd}')


def _show_help():
    print("""
  命令:
    stats        - 查看集成统计
    dashboard    - 查看用户仪表盘
    events       - 查看最近事件
    test         - 运行集成测试
    benchmark    - 运行性能基准
    help         - 显示帮助
    q            - 退出
""")


if __name__ == '__main__':
    main()
