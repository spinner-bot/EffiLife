"""
Todo-Time 联动

当 to-dos 完成任务时，自动在 time-helper 中记录时间。
"""

from typing import Optional
from datetime import datetime

from ..event_bus import Event, EventBus, EventType
from ..data_manager import DataManager
from ..api_gateway import APIGateway


class TodoTimeLinker:
    """
    待办-时间联动器

    监听 to-dos 完成事件，自动在 time-helper 中创建时间记录。
    """

    def __init__(self, gateway: Optional[APIGateway] = None, data_manager: Optional[DataManager] = None):
        self.gateway = gateway or APIGateway.get_instance()
        self.data_manager = data_manager or DataManager.get_instance()
        self.event_bus = EventBus.get_instance()

    def register(self):
        """注册事件处理器"""
        self.event_bus.subscribe(EventType.TODO_COMPLETED.value, self.on_todo_completed)
        self.event_bus.subscribe(EventType.TIME_RECORD_CREATED.value, self.on_time_record_created)

    def on_todo_completed(self, event: Event):
        """
        待办完成时

        自动在 time-helper 中记录时间。
        - 如果待办有 time_spent，记录对应时长
        - 如果没有，记录一个默认的 25 分钟（番茄钟）
        """
        # 跳过由集成系统触发的事件（避免循环）
        if event.source_module == 'integration':
            return

        todo_id = event.data.get('todo_id')
        time_spent = event.data.get('time_spent')

        if not todo_id:
            return

        time_api = self.gateway.get_module('time-helper')
        if not time_api:
            return

        # 获取待办详情
        todo_api = self.gateway.get_module('to-dos')
        todo_data = {}
        if todo_api:
            result = todo_api.get_todo(todo_id=todo_id)
            if result.get('success'):
                todo_data = result.get('data', {})

        # 确定记录时长
        if time_spent is None:
            time_spent = todo_data.get('time_spent')
        if time_spent is None:
            time_spent = todo_data.get('time_estimate', 25)

        # 确定标签
        tag = todo_data.get('category', 'default')
        title = todo_data.get('title', '完成任务')

        # 计算时间范围
        now = datetime.now()
        end_h = now.hour
        end_m = now.minute
        total_minutes = int(time_spent)
        start_minutes = end_h * 60 + end_m - total_minutes
        if start_minutes < 0:
            start_minutes = 0
        start_h = start_minutes // 60
        start_m = start_minutes % 60

        start_str = f"{start_h:02d}:{start_m:02d}"
        end_str = f"{end_h:02d}:{end_m:02d}"
        date_str = now.strftime('%Y-%m-%d')
        duration_hours = round(total_minutes / 60, 2)

        # 创建时间记录
        record = {
            '日期': date_str,
            '开始': start_str,
            '结束': end_str,
            '时长': duration_hours,
            '内容': f"[完成待办] {title}",
            '标签': tag,
            'related_todo_id': todo_id,
        }

        try:
            time_api.save_record(record, date_str)

            # 创建跨模块引用
            record_id = f"TR-{date_str}-{start_str.replace(':', '')}"
            self.data_manager.link_entities(
                source_module='time-helper',
                source_id=record_id,
                target_module='to-dos',
                target_id=todo_id,
                relation_type='tracks',
                metadata={'duration_minutes': total_minutes},
            )

            # 更新时间记录到待办
            if todo_api:
                current_spent = todo_data.get('time_spent', 0) or 0
                todo_api.update_todo(todo_id, time_spent=current_spent + total_minutes)

        except Exception as e:
            print(f"[TodoTimeLinker] Failed to record time: {e}")

    def on_time_record_created(self, event: Event):
        """
        时间记录创建时

        如果记录关联了待办，更新待办的 time_spent。
        """
        record = event.data.get('record', {})
        related_todo_id = record.get('related_todo_id')

        if not related_todo_id:
            return

        todo_api = self.gateway.get_module('to-dos')
        if not todo_api:
            return

        duration_hours = record.get('时长', 0)
        duration_minutes = int(duration_hours * 60)

        # 获取当前 time_spent
        result = todo_api.get_todo(todo_id=related_todo_id)
        if result.get('success'):
            todo_data = result.get('data', {})
            current_spent = todo_data.get('time_spent', 0) or 0
            todo_api.update_todo(
                related_todo_id,
                time_spent=current_spent + duration_minutes,
            )
