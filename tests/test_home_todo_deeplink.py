from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_home_todo_rows_preserve_the_selected_todo():
    source = HOME.read_text(encoding="utf-8")
    assert "router.push({ path: '/tasks', query: { todo: todo.id } })" in source


def test_task_center_consumes_home_todo_deeplink():
    source = TASKS.read_text(encoding="utf-8")
    assert "route.query.todo" in source
    assert "document.getElementById(`todo-${targetId}`)?.scrollIntoView" in source
