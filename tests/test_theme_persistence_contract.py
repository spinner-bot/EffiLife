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
    theme_template = source.split("<!-- 主题设置 -->", 1)[1].split("<!-- 帮助 -->", 1)[0]
    assert ':disabled="!themeDirty"' in theme_template
    assert '@click="saveTheme"' in theme_template


def test_theme_save_reports_success_and_failure_without_losing_dirty_state():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "notifyToast(t('settings.saved'), 'success')" in source
    assert "notifyToast(t('settings.saveFailed'), 'error')" in source
    assert "savedThemeSnapshot.value = cloneTheme(newConfig.theme)" in source


def test_theme_snapshot_tracks_external_settings_and_archive_changes():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "onWorkspaceChanged" in source
    assert "source !== 'settings' && source !== 'archive'" in source
    assert "const externalTheme = cloneTheme(appStore.config.theme)" in source
    assert "savedThemeSnapshot.value = externalTheme" in source
    assert "stopWorkspaceListener()" in source


def test_theme_snapshot_waits_for_external_workspace_hydration():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "void appStore.refreshWorkspaceData().then(() =>" in source
    assert "Failed to refresh theme snapshot after workspace change" in source


def test_external_theme_refresh_syncs_clean_draft_but_preserves_local_edits():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "const hadLocalDraft = themeDirty.value" in source
    assert "function syncThemeDraft(theme: Config['theme'])" in source
    assert "if (!hadLocalDraft) syncThemeDraft(externalTheme)" in source
    assert "Do not overwrite an intentional local draft" in source
