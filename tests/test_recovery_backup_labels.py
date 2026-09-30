from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "time-helper" / "desk" / "src" / "components" / "RecoveryPanel.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_recovery_panel_localizes_known_backup_types_and_keeps_unknown_fallback():
    panel = PANEL.read_text(encoding="utf-8")
    assert "const BACKUP_TYPE_KEYS" in panel
    assert "archive_import: 'settings.restore.backupArchiveImport'" in panel
    assert "return key ? t(key) : module" in panel
    assert "backupTypeLabel(backup.module)" in panel


def test_recovery_backup_labels_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "settings.restore.backupArchiveImport",
        "settings.restore.backupConfig",
        "settings.restore.backupPlans",
        "settings.restore.backupRecords",
        "settings.restore.backupScheduleRules",
        "settings.restore.backupManualPlans",
        "settings.restore.backupMigration",
    ):
        assert source.count(f"'{key}':") == 2
