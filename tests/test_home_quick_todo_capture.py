from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper/desk/src/views/HomeView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_home_can_capture_an_independent_todo_without_merging_plan_data():
    assert "async function addQuickTodo()" in HOME
    assert "await TodoService.create({ title })" in HOME
    assert '@submit.prevent="addQuickTodo"' in HOME
    assert "await refreshTodoSummary()" in HOME
    assert "notifyToast(t('home.quickTodoAdded'), 'success')" in HOME


def test_home_quick_todo_capture_has_bilingual_copy_and_narrow_layout():
    for key in ("home.quickTodoPlaceholder", "home.quickAddTodo", "home.quickTodoAdded"):
        assert I18N.count(f"'{key}':") == 2
    assert ".today-todo-capture { flex-direction: column; }" in HOME
