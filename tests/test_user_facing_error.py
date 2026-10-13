from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "services" / "userFacingError.ts").read_text(encoding="utf-8")
PLANS = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_user_facing_error_hides_storage_and_runtime_details():
    assert "indexeddb" in SOURCE
    assert "object store" in SOURCE
    assert "networkerror" in SOURCE
    assert "message.length > 240" in SOURCE


def test_plan_center_uses_safe_error_messages_for_primary_mutations():
    assert "getUserFacingError(error, t('plans.unavailable'))" in PLANS
    assert "getUserFacingError(error, t('plans.todoCreateFailed'))" in PLANS


def test_task_center_and_home_do_not_surface_raw_runtime_errors():
    assert "getUserFacingError(error, t('tasks.error.update'))" in TASKS
    assert "getUserFacingError(error, t('tasks.error.create'))" in HOME
    assert "error instanceof Error ? error.message" not in TASKS

def test_settings_recovery_paths_use_safe_error_messages():
    assert "getUserFacingError(error, t('settings.archive.localStorageUnavailable'))" in SETTINGS
    assert "(e as Error).message" not in SETTINGS
    assert "String(error)" not in SETTINGS
