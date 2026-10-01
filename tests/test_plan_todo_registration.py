from pathlib import Path

from common.api_gateway import APIGateway
from common.data_manager import DataManager
from common.event_bus import EventBus
from common.events.registry import register_all_handlers


ROOT = Path(__file__).resolve().parents[1]


def test_plan_todo_automation_is_disabled_by_default(tmp_path):
    EventBus.reset_instance()
    DataManager.reset_instance()
    try:
        handlers = register_all_handlers(
            gateway=APIGateway(),
            data_manager=DataManager(data_root=str(tmp_path)),
            event_bus=EventBus.get_instance(),
        )
        stats = EventBus.get_instance().get_stats()

        assert handlers['plan_todo_linker'] is None
        assert 'plan.created' not in stats['subscribed_types']
        assert 'plan.task_added' not in stats['subscribed_types']
        assert 'todo.completed' in stats['subscribed_types']
    finally:
        EventBus.reset_instance()
        DataManager.reset_instance()


def test_plan_todo_automation_requires_explicit_opt_in(tmp_path):
    EventBus.reset_instance()
    DataManager.reset_instance()
    try:
        handlers = register_all_handlers(
            gateway=APIGateway(),
            data_manager=DataManager(data_root=str(tmp_path)),
            event_bus=EventBus.get_instance(),
            enable_plan_todo_automation=True,
        )
        stats = EventBus.get_instance().get_stats()

        assert handlers['plan_todo_linker'] is not None
        assert 'plan.created' in stats['subscribed_types']
        assert 'plan.task_added' in stats['subscribed_types']
    finally:
        EventBus.reset_instance()
        DataManager.reset_instance()


def test_bootstrap_exposes_the_explicit_boundary_switch():
    source = (ROOT / 'common' / 'bootstrap.py').read_text(encoding='utf-8')
    assert 'enable_plan_todo_automation: bool = False' in source
    assert 'enable_plan_todo_automation=self.enable_plan_todo_automation' in source
