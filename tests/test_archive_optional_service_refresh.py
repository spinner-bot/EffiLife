from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_archive_import_refreshes_optional_runtime_services():
    settings = (DESK / "views" / "SettingsView.vue").read_text(encoding="utf-8")

    assert "AudioManager.refreshFromStorage()" in settings
    assert "EventSystem.refreshFromStorage()" in settings
    assert "CheckinSystem.refreshFromStorage()" in settings
    assert "await Promise.allSettled([" in settings


def test_optional_services_expose_durable_refresh_contract():
    audio = (DESK / "audio" / "AudioManager.ts").read_text(encoding="utf-8")
    events = (DESK / "audio" / "EventSystem.ts").read_text(encoding="utf-8")
    checkin = (DESK / "data" / "CheckinSystem.ts").read_text(encoding="utf-8")

    assert "async refreshFromStorage(): Promise<void>" in audio
    assert "async refreshFromStorage(): Promise<void>" in events
    assert "async refreshFromStorage(): Promise<void>" in checkin


def test_task_center_reloads_todo_settings_after_archive_import():
    task_center = (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")

    assert "if (source === 'settings' || source === 'archive')" in task_center
    assert "await loadTodoSettings()" in task_center
    assert "await loadCategories()" in task_center


def test_remote_archive_events_refresh_optional_services_in_the_app_shell():
    app = (DESK / "App.vue").read_text(encoding="utf-8")

    assert "if (source === 'archive')" in app
    assert "if (remote)" in app
    assert "AudioManager.refreshFromStorage()" in app
    assert "EventSystem.refreshFromStorage()" in app
    assert "CheckinSystem.refreshFromStorage()" in app


def test_backup_restore_refreshes_current_settings_state_before_reload_prompt():
    settings = (DESK / "views" / "SettingsView.vue").read_text(encoding="utf-8")
    restore_block = settings.split("async function handleRestoreBackup", 1)[1].split("async function handleEmergencyExport", 1)[0]

    assert "const result = await restoreFromSpecificBackup(backup)" in restore_block
    assert "await refreshAfterArchiveImport()" in restore_block
