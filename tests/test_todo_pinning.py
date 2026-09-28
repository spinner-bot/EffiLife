from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_pinned_todos_sort_before_priority_scored_todos_and_can_toggle():
    source = TASKS.read_text(encoding="utf-8")
    assert "if (Boolean(right.pinned) !== Boolean(left.pinned))" in source
    assert "TodoService.update(todo.id, { pinned: !todo.pinned })" in source
    assert "todo.pinned ? t('tasks.unpinTodo') : t('tasks.pinTodo')" in source


def test_todo_pin_labels_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.pinTodo", "tasks.unpinTodo"):
        assert source.count(f"'{key}'") == 2
