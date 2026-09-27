from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT = ROOT / "time-helper" / "desk" / "src" / "audio" / "EventSystem.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"


def test_event_service_hydrates_all_persistent_domains():
    source = EVENT.read_text(encoding="utf-8")

    assert "private async hydrate" in source
    for store_key, storage_key in (
        ("EVENT_SETTINGS", "'settings'"),
        ("WARNING_INBOX", "'inbox'"),
        ("EVENT_INBOX", "'inbox'"),
        ("DAILY_TRIGGER", "'trigger'"),
    ):
        assert f"STORE_NAMES.{store_key}" in source
        assert storage_key in source
    assert "async whenReady(): Promise<void>" in source


def test_event_service_keeps_legacy_mirrors_and_app_waits_for_hydration():
    source = EVENT.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")

    assert "localStorage.setItem(WARNING_INBOX_KEY" in source
    assert "localStorage.setItem(EVENT_INBOX_KEY" in source
    assert "AudioManager.whenReady(), CheckinSystem.whenReady(), EventSystem.whenReady()" in app
