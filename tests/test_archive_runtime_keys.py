from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_legacy_keys_match_runtime_services():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "DAILY_TRIGGER: 'efflife_daily_triggers'" in source
    assert "CHECKIN: 'efflife_checkin_data'" in source


def test_archive_carries_motion_settings_from_its_runtime_storage_key():
    source = ARCHIVE.read_text(encoding="utf-8")
    motion = (ROOT / "time-helper" / "desk" / "src" / "motion" / "MotionManager.ts").read_text(encoding="utf-8")
    assert "export const MOTION_SETTINGS_STORAGE_KEY = 'efflife_motion_settings'" in motion
    assert "MOTION_SETTINGS_STORAGE_KEY" in source
    assert "motionSettings: readJSON<Record<string, unknown>>(MOTION_SETTINGS_STORAGE_KEY)" in source
    assert "writeJSON(MOTION_SETTINGS_STORAGE_KEY, data.motionSettings)" in source


def test_archive_import_refreshes_motion_runtime_without_forcing_reload():
    motion = (ROOT / "time-helper" / "desk" / "src" / "motion" / "MotionManager.ts").read_text(encoding="utf-8")
    settings = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")
    assert "refreshFromStorage(): void" in motion
    assert "MotionManager.refreshFromStorage()" in settings


def test_archive_data_stats_expose_motion_settings():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "hasMotionSettings: boolean" in source
    assert "hasMotionSettings: !!readJSON(MOTION_SETTINGS_STORAGE_KEY)" in source
