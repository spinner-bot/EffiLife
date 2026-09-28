from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "time-helper" / "desk" / "src" / "storage" / "recovery.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_recovery_service_uses_localized_messages_and_locale_dates():
    source = RECOVERY.read_text(encoding="utf-8")
    assert "translate('settings.restore.suggestionBackups'" in source
    assert "translate('settings.restore.restoreFailedDetail'" in source
    assert "toLocaleString(currentLocale.value)" in source
    assert "toLocaleString('zh-CN')" not in source


def test_recovery_messages_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "settings.restore.noBackupFound",
        "settings.restore.restoredAt",
        "settings.restore.restoreFailedDetail",
        "settings.restore.emergencyRestored",
        "settings.restore.suggestionBackups",
        "settings.restore.suggestionImport",
        "settings.restore.suggestionMigration",
        "settings.restore.suggestionNoAction",
        "settings.restore.suggestionNormal",
    ):
        assert source.count(f"'{key}'") == 2
