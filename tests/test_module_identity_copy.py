from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_and_todo_entries_expose_distinct_module_identity():
    assert "t('plans.moduleLabel')" in PLANS
    assert "t('plans.moduleDescription')" in PLANS
    assert "t('tasks.moduleLabel')" in TASKS
    assert "t('tasks.moduleDescription')" in TASKS


def test_module_identity_copy_is_bilingual():
    for key in (
        "plans.moduleLabel",
        "plans.moduleDescription",
        "tasks.moduleLabel",
        "tasks.moduleDescription",
    ):
        assert f"'{key}':" in I18N
        assert I18N.count(f"'{key}':") == 2


def test_plan_copy_uses_complete_plan_semantics_instead_of_event_plan_label():
    assert "'plans.moduleLabel': '整份计划 · PH'" in I18N
    assert "'plans.moduleLabel': 'Plan documents · PH'" in I18N
    assert "'plans.moduleLabel': '事件计划 · PH'" not in I18N
    assert "'plans.moduleLabel': 'Event plans · PH'" not in I18N
