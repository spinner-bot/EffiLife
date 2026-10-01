from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_archive_import_paths_reset_busy_state_after_unexpected_errors():
    assert SETTINGS.count("finally {") >= 4
    assert SETTINGS.count("archiveBusy.value = false") >= 4
    assert SETTINGS.count("settings.archive.importFailed") >= 3


def test_browser_archive_import_does_not_reload_before_user_sees_result():
    import_block = SETTINGS.split("async function onFileSelected", 1)[1].split("// ============ 数据恢复", 1)[0]
    assert "notifyToast(result.message, result.success ? 'success' : 'error')" in import_block
    assert "result.success && await requestConfirm(result.message + '\\n\\n' + t('settings.archive.reloadConfirm'))" in import_block
