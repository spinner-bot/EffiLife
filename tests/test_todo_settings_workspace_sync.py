from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_todo_settings_broadcast_and_refresh_across_workspace_windows():
    service = SERVICE.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")
    assert "await set(STORE_NAMES.CONFIG, TODO_SETTINGS_KEY, settings)" in service
    assert "notifyWorkspaceChanged('settings')" in service
    assert "'archive', 'settings'" in tasks
    assert "if (source === 'settings')" in tasks
    assert "await loadTodoSettings()" in tasks


def test_task_center_settings_load_has_a_recoverable_error_boundary():
    tasks = TASKS.read_text(encoding="utf-8")
    load_block = tasks.split("async function loadTodoSettings()", 1)[1].split("async function saveTodoSettings", 1)[0]
    assert "try {" in load_block
    assert "TodoSettingsService.get()" in load_block
    assert "tasks.error.settings" in load_block
