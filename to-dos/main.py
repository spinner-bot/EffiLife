"""
    ============ to-dos ============
    [repository] EffLife/to-dos
    [description] 待办事项管理模块
        by spinner-bot

    轻量任务清单，专注于待办追踪与完成度管理
"""

from src import TodoAPI, TodoStorage

if __name__ == '__main__':
    print('=' * 50)
    print('  to-dos - 待办事项管理')
    print('  EffLife 效率工具集')
    print('=' * 50)

    # 初始化 API
    api = TodoAPI()

    # 显示统计
    stats = api.get_stats()
    print(f'\n📊 统计:')
    print(f'   总计: {stats["data"]["total"]} 个待办')
    print(f'   待处理: {stats["data"]["pending"]} | 进行中: {stats["data"]["in_progress"]}')
    print(f'   已完成: {stats["data"]["completed"]} | 逾期: {stats["data"]["overdue"]}')
    print(f'   完成率: {stats["data"]["completion_rate"]}%')

    # 显示分类
    categories = api.list_categories()
    print(f'\n📁 分类: {len(categories["data"])} 个')
    for cat in categories['data']:
        print(f'   • {cat["name"]} ({cat["id"]})')

    # 显示今日待办
    today = api.get_today()
    print(f'\n📅 今日待办: {today["data"]["total"]} 个')
    for item in today['data']['items'][:5]:  # 最多显示5个
        print(f'   • {item["title"]} [{item["priority"]}]')

    # 显示逾期
    overdue = api.get_overdue()
    if overdue['data']:
        print(f'\n⚠️  逾期: {len(overdue["data"])} 个')
        for item in overdue['data']:
            print(f'   • {item["title"]} (截止: {item["deadline"]})')

    print('\n' + '=' * 50)
    print('  输入 python -m src.cli 进入交互模式')
    print('=' * 50)
