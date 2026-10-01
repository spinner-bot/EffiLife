from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_center_exposes_safe_bulk_actions():
    source = TASKS.read_text(encoding="utf-8")
    assert "async function bulkCompleteTodos()" in source
    assert "async function bulkDeleteTodos()" in source
    assert "DataService.unlinkTodoFromRecords(todo.id)" in source
    assert "completePlanTask" not in source
    assert "clearTodoSelection()" in source
    assert "t('tasks.bulkDeleteConfirm'" in source


def test_bulk_task_messages_have_both_locale_catalog_entries():
    source = I18N.read_text(encoding="utf-8")
    keys = (
        "tasks.selectVisible",
        "tasks.selectedCount",
        "tasks.bulkComplete",
        "tasks.bulkDelete",
        "tasks.bulkDeleteConfirm",
        "tasks.bulkPlanSyncFailed",
    )
    for key in keys:
        assert source.count(f"'{key}':") == 2
