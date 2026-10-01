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


def test_legacy_todo_import_waits_for_reload_confirmation_after_success():
    import_block = SETTINGS.split("async function onLegacyTodoSelected", 1)[1].split("const backupsList", 1)[0]
    assert "notifyToast(t('settings.archive.legacyTodoImportSuccess', { ...result }), 'success')" in import_block
    assert "if (await requestConfirm(t('settings.archive.reloadNow')))" in import_block


def test_archive_controls_announce_busy_state_and_refresh_stats_on_entry():
    assert 'class="archive-actions" :aria-busy="archiveBusy"' in SETTINGS
    assert 'role="status" aria-live="polite"' in SETTINGS
    assert "settings.archive.busy" in SETTINGS
    assert "watch(currentView, (view) =>" in SETTINGS
    assert "if (view === 'archive') void refreshDataStats()" in SETTINGS
    assert "if (currentView.value === 'archive') void refreshDataStats()" in SETTINGS


def test_archive_stats_do_not_present_zero_values_when_storage_read_fails():
    assert "const dataStatsUnavailable = ref(false)" in SETTINGS
    assert "dataStatsUnavailable.value = true" in SETTINGS
    assert 'class="archive-stats-unavailable" role="status" aria-live="polite"' in SETTINGS
    assert "@click=\"refreshDataStats\"" in SETTINGS
