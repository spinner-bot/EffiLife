from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_archive_import_paths_reset_busy_state_after_unexpected_errors():
    assert SETTINGS.count("finally {") >= 4
    assert SETTINGS.count("archiveBusy.value = false") >= 4
    assert SETTINGS.count("settings.archive.importFailed") >= 3
