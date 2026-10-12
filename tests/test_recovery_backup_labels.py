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


def test_recovery_panel_exposes_confirmed_single_backup_deletion():
    panel = PANEL.read_text(encoding="utf-8")
    settings = (ROOT / "time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")
    i18n = I18N.read_text(encoding="utf-8")
    assert "delete: [backup: BackupData]" in panel
    assert "$emit('delete', backup)" in panel
    assert "deleteBackup(backup.module, backup.timestamp)" in settings
    assert "settings.restore.deleteConfirm" in settings
    assert i18n.count("'settings.restore.delete':") == 2
