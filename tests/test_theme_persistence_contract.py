from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_theme_changes_preview_and_save_automatically_on_exit():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "appStore.previewConfig({ ...config.value, theme })" in source
    assert "const themeDirty = computed" in source
    assert "if (currentView.value === 'theme' && themeDirty.value)" in source
    assert "const saved = await saveTheme()" in source
    assert "if (!saved) return" in source
    assert "onBeforeRouteLeave(async () =>" in source
    assert "if (currentView.value !== 'theme' || !themeDirty.value) return true" in source


def test_theme_save_refreshes_persistent_snapshot():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "await appStore.saveConfig(newConfig)" in source
    assert "savedThemeSnapshot.value = cloneTheme(newConfig.theme)" in source
    theme_template = source.split("<!-- 主题设置 -->", 1)[1].split("<!-- 帮助 -->", 1)[0]
    assert '@click="saveTheme"' not in theme_template


def test_theme_preview_status_explains_automatic_save_in_both_locales():
    source = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    assert source.count("'settings.theme.previewStatus'") == 2
    assert "退出主题面板时自动保存" in source
    assert "save automatically when leaving" in source


def test_theme_save_reports_success_and_failure_without_losing_dirty_state():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "notifyToast(t('settings.saved'), 'success')" in source
    assert "notifyToast(t('settings.saveFailed'), 'error')" in source
    assert "savedThemeSnapshot.value = cloneTheme(newConfig.theme)" in source


def test_theme_editor_owns_detached_draft_objects():
    source = SETTINGS.read_text(encoding="utf-8")

    assert "const solidConfig = ref<SolidThemeConfig>(config.value.theme.solid ? { ...config.value.theme.solid }" in source
    assert "const gradientConfig = ref<GradientThemeConfig>(config.value.theme.gradient ? { ...config.value.theme.gradient }" in source
    assert "const glassConfig = ref<GlassThemeConfig>(config.value.theme.glass ? { ...config.value.theme.glass }" in source
    assert "const neonConfig = ref<NeonThemeConfig>(config.value.theme.neon ? { ...config.value.theme.neon }" in source
    assert "solid: { ...solidConfig.value }" in source
    assert "gradient: { ...gradientConfig.value }" in source
    assert "glass: { ...glassConfig.value }" in source
    assert "neon: { ...neonConfig.value }" in source


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


def test_generic_config_watcher_does_not_overwrite_theme_draft():
    source = SETTINGS.read_text(encoding="utf-8")
    config_watch = source.split("watch(() => config.value", 1)[1].split("watch([themeType", 1)[0]
    assert "overtimeThreshold.value = newConfig.overtime_threshold" in config_watch
    assert "showAmPm.value = newConfig.show_ampm" in config_watch
    assert "themeType.value = newConfig.theme.type" not in config_watch
    assert "syncThemeDraft(newConfig.theme)" not in config_watch
