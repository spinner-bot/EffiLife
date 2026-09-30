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
