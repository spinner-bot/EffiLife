from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_restore_confirmation_uses_current_locale_for_timestamp():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "new Date(backup.timestamp).toLocaleString(locale.value)" in source
