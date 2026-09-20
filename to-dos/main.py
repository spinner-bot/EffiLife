"""
    ============ to-dos ============
    [repository] EffLife/to-dos
    [description] 待办事项管理模块
        by spinner-bot

    轻量任务清单，专注于待办追踪与完成度管理
"""

import sys
from pathlib import Path

# 确保 src 包可导入
sys.path.insert(0, str(Path(__file__).parent))

from src import TodoAPI, TodoStorage, Priority, TodoStatus, PRIORITY_LABELS, STATUS_LABELS


def show_banner():
    print('=' * 50)
    print('  to-dos - 待办事项管理 v0.1.0')
    print('  EffLife 效率工具集')
    print('=' * 50)


def show_dashboard(api: TodoAPI):
    """显示概览面板"""
    # 统计
    stats = api.get_stats()
    if stats['success']:
        d = stats['data']
        print(f'\n  统计: 总计 {d["total"]} | 待处理 {d["pending"]} | 进行中 {d["in_progress"]}')
        print(f'  已完成 {d["completed"]} | 逾期 {d["overdue"]} | 完成率 {d["completion_rate"]}%')

    # 分类
    categories = api.list_categories()
    if categories['success']:
        cats = categories['data']
        print(f'\n  分类 ({len(cats)}): ', end='')
        print(' | '.join(f'{c["name"]}({c["id"]})' for c in cats))

    # 今日待办
    today = api.get_today()
    if today['success'] and today['data']:
        items = today['data']
        if isinstance(items, dict):
            items = items.get('items', [])
        print(f'\n  今日待办 ({len(items)}):')
        for item in items[:5]:
            title = item.get('title', item.get('id', '?'))
            pri = item.get('priority', 'normal')
            print(f'    - {title} [{pri}]')

    # 逾期
    overdue = api.get_overdue()
    if overdue['success'] and overdue['data']:
        items = overdue['data']
        if isinstance(items, dict):
            items = items.get('items', [])
        print(f'\n  逾期 ({len(items)}):')
        for item in items[:5]:
            title = item.get('title', item.get('id', '?'))
            dl = item.get('deadline', item.get('due_date', '?'))[:10]
            print(f'    ! {title} (截止: {dl})')


def interactive_loop(api: TodoAPI):
    """交互式命令行"""
    show_banner()
    show_dashboard(api)
    print('\n  输入 help 查看命令, q 退出\n')

    while True:
        try:
            cmd = input('  to-dos> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\n  再见!')
            break

        if not cmd:
            continue

        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if action in ('q', 'quit', 'exit'):
            print('  再见!')
            break

        elif action in ('h', 'help'):
            _print_help()

        elif action in ('list', 'ls'):
            _cmd_list(api, args)

        elif action == 'add':
            _cmd_add(api, args)

        elif action == 'done':
            _cmd_done(api, args)

        elif action == 'cancel':
            _cmd_cancel(api, args)

        elif action in ('rm', 'delete'):
            _cmd_delete(api, args)

        elif action == 'show':
            _cmd_show(api, args)

        elif action == 'overdue':
            _cmd_overdue(api)

        elif action == 'today':
            _cmd_today(api)

        elif action == 'stats':
            _cmd_stats(api)

        elif action in ('cats', 'categories'):
            _cmd_cats(api)

        elif action == 'search':
            _cmd_search(api, args)

        elif action == 'sub':
            _cmd_subtask(api, args)

        else:
            print(f'  未知命令: {action}')


def _print_help():
    print("""
  命令:
    list [status]     - 列出待办 (all/pending/progress/done/archived)
    add <标题>        - 添加待办
    done <id>         - 完成待办
    cancel <id>       - 取消待办
    rm <id>           - 删除(归档)待办
    show <id>         - 显示详情
    overdue           - 显示逾期
    today             - 显示今日待办
    stats             - 统计信息
    cats              - 列出分类
    search <关键词>   - 搜索
    sub <id> <标题>   - 添加子任务
    help              - 显示帮助
    q                 - 退出
""")


def _cmd_list(api, status):
    status_map = {
        '': None, 'all': None,
        'pending': 'pending',
        'progress': 'in-progress',
        'done': 'completed',
        'archived': 'archived',
        'cancelled': 'cancelled',
    }
    s = status.strip().lower()
    if s not in status_map:
        print(f'  无效状态: {s}')
        return

    result = api.list_todos(status=status_map[s])
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return

    items = result['data']['items']
    if not items:
        print('  (暂无待办)')
        return

    print(f'\n  共 {len(items)} 个待办:')
    for item in items[:30]:
        si = {'pending': 'O', 'in-progress': 'P', 'completed': 'V', 'archived': 'A', 'cancelled': 'X'}.get(item['status'], '?')
        pi = {'urgent-important': '!!', 'important': '! ', 'urgent': '! ', 'normal': '  '}.get(item['priority'], '  ')
        dl = item.get('deadline', '')[:10] if item.get('deadline') else ''
        print(f'  [{si}] {pi} [{item["id"]}] {item["title"]}  {dl}')

    if len(items) > 30:
        print(f'  ... 还有 {len(items) - 30} 个')


def _cmd_add(api, title):
    if not title:
        print('  用法: add <标题>')
        return
    result = api.create_todo(title=title)
    if result['success']:
        print(f'  + 创建成功: {result["data"]["id"]}')
    else:
        print(f'  x 创建失败: {result["message"]}')


def _cmd_done(api, todo_id):
    if not todo_id:
        print('  用法: done <ID>')
        return
    result = api.complete_todo(todo_id.strip())
    if result['success']:
        print(f'  * 已完成: {todo_id}')
    else:
        print(f'  x 失败: {result["message"]}')


def _cmd_cancel(api, todo_id):
    if not todo_id:
        print('  用法: cancel <ID>')
        return
    result = api.cancel_todo(todo_id.strip())
    if result['success']:
        print(f'  x 已取消: {todo_id}')
    else:
        print(f'  x 失败: {result["message"]}')


def _cmd_delete(api, todo_id):
    if not todo_id:
        print('  用法: rm <ID>')
        return
    result = api.delete_todo(todo_id.strip())
    if result['success']:
        print(f'  - 已归档: {todo_id}')
    else:
        print(f'  x 失败: {result["message"]}')


def _cmd_show(api, todo_id):
    if not todo_id:
        print('  用法: show <ID>')
        return
    result = api.get_todo(todo_id.strip())
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return

    item = result['data']
    print(f'\n  {"=" * 40}')
    print(f'  {item["title"]}')
    print(f'  {"=" * 40}')
    print(f'  ID:       {item["id"]}')
    print(f'  状态:     {item["status"]}')
    print(f'  优先级:   {item["priority"]}')
    print(f'  分类:     {item.get("category", "-")}')
    print(f'  创建:     {item["created_at"][:19]}')
    print(f'  更新:     {item["updated_at"][:19]}')
    if item.get('deadline'):
        print(f'  截止:     {item["deadline"][:19]}')
    if item.get('description'):
        print(f'  描述:     {item["description"]}')
    if item.get('tags'):
        print(f'  标签:     {", ".join(item["tags"])}')
    if item.get('subtasks'):
        print(f'  子任务 ({len(item["subtasks"])}):')
        for s in item['subtasks']:
            done = 'V' if s.get('completed') else 'O'
            print(f'    [{done}] {s["title"]}')
    print()


def _cmd_overdue(api):
    result = api.get_overdue()
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return
    items = result['data']
    if not items:
        print('  OK 没有逾期待办')
        return
    print(f'\n  逾期 {len(items)} 个:')
    for item in items:
        dl = item.get('deadline', '?')[:10]
        print(f'  ! [{item["id"]}] {item["title"]} (截止: {dl})')


def _cmd_today(api):
    result = api.get_today()
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return
    items = result['data']
    if isinstance(items, dict):
        items = items.get('items', [])
    if not items:
        print('  今日暂无待办')
        return
    print(f'\n  今日 {len(items)} 个:')
    for item in items:
        print(f'  - [{item["id"]}] {item["title"]}')


def _cmd_stats(api):
    result = api.get_stats()
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return
    d = result['data']
    print(f'\n  ====== 统计 ======')
    print(f'  总计: {d["total"]}')
    print(f'  待处理: {d["pending"]} | 进行中: {d["in_progress"]}')
    print(f'  已完成: {d["completed"]} | 已归档: {d["archived"]} | 已取消: {d["cancelled"]}')
    print(f'  逾期: {d["overdue"]} | 完成率: {d["completion_rate"]}%')
    if d.get('by_category'):
        print(f'  按分类:')
        for cat, count in d['by_category'].items():
            print(f'    {cat}: {count}')
    if d.get('by_priority'):
        print(f'  按优先级:')
        for pri, count in d['by_priority'].items():
            print(f'    {pri}: {count}')


def _cmd_cats(api):
    result = api.list_categories()
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return
    cats = result['data']
    print(f'\n  分类 ({len(cats)} 个):')
    for cat in cats:
        print(f'  {cat["color"]} | {cat["name"]} [{cat["id"]}]')


def _cmd_search(api, keyword):
    if not keyword:
        print('  用法: search <关键词>')
        return
    result = api.list_todos(search=keyword)
    if not result['success']:
        print(f'  错误: {result["message"]}')
        return
    items = result['data']['items']
    if not items:
        print(f'  未找到: {keyword}')
        return
    print(f'\n  搜索 "{keyword}" - {len(items)} 个结果:')
    for item in items:
        print(f'  - [{item["id"]}] {item["title"]}')


def _cmd_subtask(api, args):
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        print('  用法: sub <todo_id> <子任务标题>')
        return
    todo_id, title = parts
    result = api.add_subtask(todo_id.strip(), title.strip())
    if result['success']:
        print(f'  + 子任务已添加: {result["data"]["title"]}')
    else:
        print(f'  x 失败: {result["message"]}')


def main():
    """主入口"""
    # 初始化 API
    api = TodoAPI()

    if len(sys.argv) > 1:
        # 非交互模式
        cmd = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []

        if cmd == 'stats':
            _cmd_stats(api)
        elif cmd in ('list', 'ls'):
            _cmd_list(api, args[0] if args else '')
        elif cmd == 'add' and args:
            _cmd_add(api, ' '.join(args))
        elif cmd == 'done' and args:
            _cmd_done(api, args[0])
        elif cmd == 'overdue':
            _cmd_overdue(api)
        elif cmd == 'today':
            _cmd_today(api)
        elif cmd == 'search' and args:
            _cmd_search(api, ' '.join(args))
        else:
            print(f'  未知命令: {cmd}')
    else:
        # 交互模式
        interactive_loop(api)


if __name__ == '__main__':
    main()
