"""
to-dos 命令行交互界面
"""

import sys
from . import TodoAPI, Priority, TodoStatus, PRIORITY_LABELS, STATUS_LABELS


class TodoCLI:
    """命令行交互界面"""

    def __init__(self):
        self.api = TodoAPI()

    def run(self):
        """启动交互模式"""
        print('=' * 50)
        print('  to-dos 交互模式')
        print('=' * 50)
        self._help()

        while True:
            try:
                cmd = input('\n> ').strip()
                if not cmd:
                    continue
                if cmd in ('quit', 'exit', 'q'):
                    print('再见！')
                    break
                self._process_command(cmd)
            except KeyboardInterrupt:
                print('\n再见！')
                break
            except EOFError:
                break

    def _help(self):
        """显示帮助"""
        print('\n命令:')
        print('  list [status]          列出待办 (status: all/pending/done)')
        print('  add <title>            添加待办')
        print('  done <id>              完成待办')
        print('  rm <id>                删除待办')
        print('  show <id>              显示详情')
        print('  overdue                显示逾期')
        print('  today                  显示今日')
        print('  stats                  统计信息')
        print('  cats                   列出分类')
        print('  help                   显示帮助')
        print('  quit                   退出')

    def _process_command(self, cmd: str):
        """处理命令"""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if command == 'list':
            self._cmd_list(args)
        elif command == 'add':
            self._cmd_add(args)
        elif command == 'done':
            self._cmd_done(args)
        elif command == 'rm':
            self._cmd_rm(args)
        elif command == 'show':
            self._cmd_show(args)
        elif command == 'overdue':
            self._cmd_overdue()
        elif command == 'today':
            self._cmd_today()
        elif command == 'stats':
            self._cmd_stats()
        elif command == 'cats':
            self._cmd_cats()
        elif command in ('help', 'h', '?'):
            self._help()
        else:
            print(f'未知命令: {command}')

    def _cmd_list(self, status: str):
        """列出待办"""
        status_map = {
            '': None,
            'all': None,
            'pending': 'pending',
            'progress': 'in-progress',
            'done': 'completed',
            'archived': 'archived',
        }
        status_val = status_map.get(status.lower())
        if status.lower() not in status_map:
            print(f'无效状态: {status}')
            return

        result = self.api.list_todos(status=status_val)
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        items = result['data']['items']
        if not items:
            print('暂无待办事项')
            return

        print(f'\n共 {len(items)} 个待办:')
        for item in items[:20]:  # 最多显示20个
            status_icon = {
                'pending': '○',
                'in-progress': '◐',
                'completed': '●',
                'archived': '✓',
                'cancelled': '✗',
            }.get(item['status'], '?')

            priority_icon = {
                'urgent-important': '🔴',
                'important': '🟠',
                'urgent': '🟡',
                'normal': '⚪',
            }.get(item['priority'], '⚪')

            deadline = item.get('deadline', '')[:10] if item.get('deadline') else ''
            print(f'  {status_icon} {priority_icon} [{item["id"]}] {item["title"]}  {deadline}')

        if len(items) > 20:
            print(f'  ... 还有 {len(items) - 20} 个')

    def _cmd_add(self, title: str):
        """添加待办"""
        if not title:
            print('用法: add <标题>')
            return

        result = self.api.create_todo(title=title)
        if result['success']:
            print(f'✓ 创建成功: {result["data"]["id"]}')
        else:
            print(f'✗ 创建失败: {result["message"]}')

    def _cmd_done(self, todo_id: str):
        """完成待办"""
        if not todo_id:
            print('用法: done <ID>')
            return

        result = self.api.complete_todo(todo_id)
        if result['success']:
            print(f'✓ 已完成: {todo_id}')
        else:
            print(f'✗ 失败: {result["message"]}')

    def _cmd_rm(self, todo_id: str):
        """删除待办"""
        if not todo_id:
            print('用法: rm <ID>')
            return

        result = self.api.delete_todo(todo_id)
        if result['success']:
            print(f'✓ 已归档: {todo_id}')
        else:
            print(f'✗ 失败: {result["message"]}')

    def _cmd_show(self, todo_id: str):
        """显示详情"""
        if not todo_id:
            print('用法: show <ID>')
            return

        result = self.api.get_todo(todo_id)
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        item = result['data']
        print(f'\n{'='*40}')
        print(f'  {item["title"]}')
        print(f'{'='*40}')
        print(f'  ID: {item["id"]}')
        print(f'  状态: {STATUS_LABELS.get(TodoStatus(item["status"]), item["status"])}')
        print(f'  优先级: {PRIORITY_LABELS.get(Priority(item["priority"]), item["priority"])}')
        print(f'  创建: {item["created_at"][:19]}')
        print(f'  更新: {item["updated_at"][:19]}')
        if item.get('deadline'):
            print(f'  截止: {item["deadline"][:19]}')
        if item.get('description'):
            print(f'  描述: {item["description"]}')
        if item.get('tags'):
            print(f'  标签: {", ".join(item["tags"])}')
        if item.get('subtasks'):
            print(f'  子任务:')
            for s in item['subtasks']:
                status = '✓' if s.get('completed') else '○'
                print(f'    {status} {s["title"]}')

    def _cmd_overdue(self):
        """显示逾期"""
        result = self.api.get_overdue()
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        items = result['data']
        if not items:
            print('✓ 没有逾期待办')
            return

        print(f'\n⚠️  逾期 {len(items)} 个:')
        for item in items:
            print(f'  • [{item["id"]}] {item["title"]} (截止: {item["deadline"][:10]})')

    def _cmd_today(self):
        """显示今日"""
        result = self.api.get_today()
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        items = result['data']
        if not items:
            print('今日暂无待办')
            return

        print(f'\n📅 今日 {len(items)} 个:')
        for item in items:
            print(f'  • [{item["id"]}] {item["title"]}')

    def _cmd_stats(self):
        """统计信息"""
        result = self.api.get_stats()
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        data = result['data']
        print(f'\n📊 统计:')
        print(f'  总计: {data["total"]}')
        print(f'  待处理: {data["pending"]} | 进行中: {data["in_progress"]}')
        print(f'  已完成: {data["completed"]} | 已归档: {data["archived"]}')
        print(f'  逾期: {data["overdue"]} | 完成率: {data["completion_rate"]}%')

        if data.get('by_category'):
            print(f'\n  按分类:')
            for cat, count in data['by_category'].items():
                print(f'    {cat}: {count}')

    def _cmd_cats(self):
        """列出分类"""
        result = self.api.list_categories()
        if not result['success']:
            print(f'错误: {result["message"]}')
            return

        categories = result['data']
        print(f'\n📁 分类 ({len(categories)} 个):')
        for cat in categories:
            print(f'  • {cat["name"]} [{cat["id"]}] - {cat["color"]}')


def main():
    """CLI 入口"""
    cli = TodoCLI()
    cli.run()


if __name__ == '__main__':
    main()
