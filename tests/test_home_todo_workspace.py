from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_home_reads_and_sorts_active_todos_for_summary():
    source = HOME.read_text(encoding="utf-8")
    assert "const todayTodos = ref<UnifiedTodo[]>([])" in source
    assert "TodoService.list()" in source
    assert "todayTodos.value = [...active]" in source
    assert ".slice(0, 3)" in source
    assert "router.push('/tasks')" in source


def test_home_todo_workspace_has_bilingual_copy():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "home.todayTodosEyebrow",
        "home.todayTodos",
        "home.viewTodos",
        "home.noTodos",
        "home.createTodoHint",
        "home.openTodoCenter",
        "home.noDeadline",
        "home.moreTodos",
    ):
        assert source.count(f"'{key}'") == 2
