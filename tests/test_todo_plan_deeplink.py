from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_task_center_opens_linked_ph_task_without_merging_domains():
    assert "function openLinkedPlan(todo: UnifiedTodo)" in VIEW
    assert "path: '/plans'" in VIEW
    assert "plan: String(todo.related_plan_id)" in VIEW
    assert "task: String(todo.related_plan_task_id)" in VIEW
    assert "@click=\"openLinkedPlan(todo)\"" in VIEW


def test_linked_plan_action_is_localized():
    assert "'tasks.openPlan': '打开关联计划任务'" in I18N
    assert "'tasks.openPlan': 'Open linked plan task'" in I18N
