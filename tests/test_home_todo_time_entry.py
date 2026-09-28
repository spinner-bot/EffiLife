from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_home_todo_rows_expose_time_progress_and_a_record_entry():
    source = HOME.read_text(encoding="utf-8")
    assert "function openTodoRecord(todo: UnifiedTodo)" in source
    assert "path: '/records', query: { todo: todo.id }" in source
    assert "formatTodoTime(todo)" in source
    assert "home.recordTodoTime" in source


def test_home_todo_time_entry_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'home.timeProgress':") == 2
    assert source.count("'home.recordTodoTime':") == 2
