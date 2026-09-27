from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "time-helper" / "desk" / "src" / "audio" / "AudioManager.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
CHECKIN = ROOT / "time-helper" / "desk" / "src" / "data" / "CheckinSystem.ts"


def test_audio_settings_hydrate_from_indexeddb_without_breaking_sync_api():
    source = AUDIO.read_text(encoding="utf-8")

    assert "private async hydrateSettings" in source
    assert "STORE_NAMES.AUDIO_SETTINGS, 'settings'" in source
    assert "async whenReady(): Promise<void>" in source
    assert "private settingsRevision = 0" in source


def test_audio_settings_keep_legacy_mirror_and_persist_primary_store():
    source = AUDIO.read_text(encoding="utf-8")

    assert "localStorage.setItem('efflife_audio_settings'" in source
    assert "await set(STORE_NAMES.AUDIO_SETTINGS, 'settings', this.settings.value)" in source


def test_app_waits_for_audio_hydration_before_runtime_checks():
    source = APP.read_text(encoding="utf-8")
    assert "AudioManager.whenReady()" in source
    assert "CheckinSystem.whenReady()" in source


def test_checkin_settings_hydrate_and_persist_in_indexeddb():
    source = CHECKIN.read_text(encoding="utf-8")
    assert "private async hydrate" in source
    assert "STORE_NAMES.CHECKIN, 'data'" in source
    assert "async whenReady(): Promise<void>" in source
    assert "private dataRevision = 0" in source
