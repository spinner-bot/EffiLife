from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"
APP = (DESK / "App.vue").read_text(encoding="utf-8")
TASKS = (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
SERVICE = (DESK / "services" / "focusSessionService.ts").read_text(encoding="utf-8")


def test_focus_session_is_durable_and_versioned():
    assert "effilife.focus-session.v1" in SERVICE
    assert "todoId" in SERVICE and "todoTitle" in SERVICE and "startedAt" in SERVICE
    assert "JSON.parse(raw)" in SERVICE
    assert "window.localStorage.removeItem(STORAGE_KEY)" in SERVICE
    assert "onChange(handler" in SERVICE


def test_task_center_restores_and_clears_session_only_after_successful_recording():
    assert "FocusSessionService.start" in TASKS
    assert "restoreFocusSession" in TASKS
    assert "const saved = await persistTodoTime(todo, minutes, startedAt)" in TASKS
    assert "if (!saved) return" in TASKS
    assert "FocusSessionService.clear()" in TASKS
    assert "command === 'start'" in TASKS


def test_shell_exposes_active_focus_on_desktop_and_mobile_routes():
    assert "activeFocusSession" in APP
    assert "active-focus-bar" in APP
    assert "stopActiveFocus" in APP
    assert "path: '/tasks', query: { todo: session.todoId, focus: 'stop' }" in APP
    assert "@media (max-width: 600px)" in APP


def test_home_todo_can_enter_the_unified_focus_session():
    home = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert "function openTodoFocus" in home
    assert "FocusSessionService.get()" in home
    assert "query: { todo: todo.id, focus: 'start' }" in home
    assert 'class="today-todo-focus"' in home


def test_home_plan_task_can_enter_the_unified_focus_session_without_merging_domains():
    home = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert "function startFocusPlan" in home
    assert "related_plan_id: String(item.planId)" in home
    assert "related_plan_task_id: item.task.internal_id" in home
    assert "query: { todo: todo.id, focus: 'start' }" in home
    assert 'class="focus-plan-focus"' in home
