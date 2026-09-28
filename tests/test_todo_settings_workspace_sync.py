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

