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

