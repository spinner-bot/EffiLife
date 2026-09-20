"""
Plan-Todo 联动

当 plan-helper 创建计划或添加任务时，自动在 to-dos 中创建关联的待办事项。
"""

from typing import Optional
from ..event_bus import Event, EventBus, EventType
from ..data_manager import DataManager
from ..api_gateway import APIGateway


class PlanTodoLinker:
    """
    计划-待办联动器

    监听 plan-helper 事件，自动创建/更新 to-dos 中的关联待办。
    """

    def __init__(self, gateway: Optional[APIGateway] = None, data_manager: Optional[DataManager] = None):
        self.gateway = gateway or APIGateway.get_instance()
        self.data_manager = data_manager or DataManager.get_instance()
        self.event_bus = EventBus.get_instance()

    def register(self):
        """注册事件处理器"""
        self.event_bus.subscribe(EventType.PLAN_CREATED.value, self.on_plan_created)
        self.event_bus.subscribe(EventType.PLAN_TASK_ADDED.value, self.on_plan_task_added)
        self.event_bus.subscribe(EventType.PLAN_TASK_COMPLETED.value, self.on_plan_task_completed)
        self.event_bus.subscribe(EventType.PLAN_COMPLETED.value, self.on_plan_completed)

    def on_plan_created(self, event: Event):
        """
        计划创建时

        如果事件数据中包含 auto_create_todos=True，则自动为每个任务创建待办。
        """
        plan_id = event.data.get('plan_id')
        auto_create = event.data.get('auto_create_todos', False)
        tasks = event.data.get('tasks', [])

        if not auto_create or not tasks:
            return

        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return

        created_todos = []
        for task in tasks:
            title = task.get('content', task.get('title', ''))
            if not title:
                continue

            result = todo_api.create_todo(
                title=title,
                related_plan_id=str(plan_id),
                time_estimate=task.get('time_minutes'),
                priority=task.get('priority', 'normal'),
                category=task.get('category', 'default'),
            )

            if result.get('success'):
                todo_data = result.get('data', {})
                todo_id = todo_data.get('id', '')
                created_todos.append(todo_id)

                # 创建跨模块引用
                self.data_manager.link_entities(
                    source_module='to-dos',
                    source_id=todo_id,
                    target_module='plan-helper',
                    target_id=str(plan_id),
                    relation_type='belongs_to',
                )

        return {
            'plan_id': plan_id,
            'created_todos': created_todos,
            'count': len(created_todos),
        }

    def on_plan_task_added(self, event: Event):
        """任务添加到计划时，自动创建对应待办"""
        plan_id = event.data.get('plan_id')
        task_content = event.data.get('content', '')
        task_id = event.data.get('task_id', '')
        auto_todo = event.data.get('auto_todo', False)

        if not auto_todo or not task_content:
            return

        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return

        result = todo_api.create_todo(
            title=task_content,
            related_plan_id=str(plan_id),
        )

        if result.get('success'):
            todo_id = result.get('data', {}).get('id', '')
            self.data_manager.link_entities(
                source_module='to-dos',
                source_id=todo_id,
                target_module='plan-helper',
                target_id=str(plan_id),
                relation_type='belongs_to',
                metadata={'plan_task_id': task_id},
            )

            # 发布待办创建事件
            self.event_bus.emit(
                event_type=EventType.TODO_CREATED.value,
                source_module='integration',
                data={
                    'todo_id': todo_id,
                    'related_plan_id': str(plan_id),
                    'triggered_by': 'plan_task_added',
                },
            )

    def on_plan_task_completed(self, event: Event):
        """计划任务完成时，更新关联待办状态"""
        plan_id = event.data.get('plan_id')
        task_id = event.data.get('task_id')

        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return

        # 查找关联的待办
        linked_todo_ids = self.data_manager.find_linked_ids(
            source_id=str(plan_id),
            target_module='to-dos',
        )

        # 反向查找：通过 plan_task_id 元数据
        refs = self.data_manager.get_references_by_target(str(plan_id))
        for ref in refs:
            if ref.metadata.get('plan_task_id') == task_id:
                todo_id = ref.source_id
                result = todo_api.complete_todo(todo_id)
                if result.get('success'):
                    self.event_bus.emit(
                        event_type=EventType.TODO_COMPLETED.value,
                        source_module='integration',
                        data={
                            'todo_id': todo_id,
                            'triggered_by': 'plan_task_completed',
                        },
                    )
                break

    def on_plan_completed(self, event: Event):
        """计划完成时，批量完成所有关联待办"""
        plan_id = event.data.get('plan_id')

        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return

        # 获取计划关联的所有待办
        result = todo_api.get_todos_by_plan(plan_id=str(plan_id))
        if not result.get('success'):
            return

        todos_data = result.get('data', {})
        todos = todos_data.get('items', []) if isinstance(todos_data, dict) else []

        completed_count = 0
        for todo in todos:
            if todo.get('status') != 'completed':
                complete_result = todo_api.complete_todo(todo['id'])
                if complete_result.get('success'):
                    completed_count += 1

        return {
            'plan_id': plan_id,
            'completed_todos': completed_count,
        }
