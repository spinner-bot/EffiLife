from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_archive_preview_discloses_stale_or_local_plan_snapshot_source():
    assert "const planStatusWarning = preview.planStatus === 'snapshot' || preview.planStatus === 'stale'" in SETTINGS
    assert "t('settings.archive.planSnapshotLocalExportWarning')" in SETTINGS
    assert ".filter(Boolean)" in SETTINGS
    assert ".join('\\n')" in SETTINGS
