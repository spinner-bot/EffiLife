from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_theme_changes_preview_before_save_and_confirm_on_exit():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "appStore.previewConfig({ ...config.value, theme })" in source
    assert "const themeDirty = computed" in source
    assert "if (currentView.value === 'theme' && themeDirty.value)" in source
    assert "await requestConfirm(t('settings.theme.unsavedConfirm'))" in source


def test_theme_save_refreshes_persistent_snapshot():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "await appStore.saveConfig(newConfig)" in source
    assert "savedThemeSnapshot.value = cloneTheme(newConfig.theme)" in source
    assert "function discardThemeChanges()" in source
    assert ':disabled="!themeDirty"' in source
    assert '@click="saveTheme"' in source


def test_theme_save_reports_success_and_failure_without_losing_dirty_state():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "notifyToast(t('settings.saved'), 'success')" in source
    assert "notifyToast(t('settings.saveFailed'), 'error')" in source
    assert "savedThemeSnapshot.value = cloneTheme(newConfig.theme)" in source
