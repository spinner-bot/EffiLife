from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_record_list_opens_the_linked_todo_workspace():
    source = RECORDS.read_text(encoding="utf-8")
    assert "function openLinkedTodo(todoId: string)" in source
    assert "path: '/tasks', query: { todo: todoId }" in source
    assert "@click=\"openLinkedTodo(record.todo_id)\"" in source


def test_record_route_can_preselect_a_todo_for_a_new_time_record():
    source = RECORDS.read_text(encoding="utf-8")
    assert "route.query.todo" in source
    assert "openAddForm()" in source
    assert "selectedTodoId.value = linkedTodoFromQuery.value" in source


def test_record_todo_navigation_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'records.openTodo':") == 2
