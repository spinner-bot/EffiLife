from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_theme_changes_preview_and_confirm_before_persisting_on_exit():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "appStore.previewConfig({ ...config.value, theme })" in source
    assert "const themeDirty = computed" in source
    assert "async function confirmThemeExit()" in source
    assert "requestConfirm(t('settings.theme.unsavedConfirm'))" in source
    assert "return await flushThemeSave()" in source
    assert "return await saveTheme()" in source
    assert "queueThemeSave" not in source
    assert "onBeforeRouteLeave(async () =>" in source
    assert "if (currentView.value !== 'theme' || !themeDirty.value) return true" in source


def test_theme_cards_expose_visual_previews_and_selection_semantics():
    source = SETTINGS.read_text(encoding="utf-8")
    assert ':aria-pressed="themeType === theme.type"' in source
    assert 'class="theme-swatch"' in source
    assert ':style="{ background: theme.preview }"' in source


def test_theme_save_refreshes_persistent_snapshot_without_a_save_button():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "await appStore.saveConfig(newConfig)" in source
    assert "await appStore.refreshWorkspaceData()" in source
    assert "const persistedTheme = cloneTheme(appStore.config.theme)" in source
    assert "savedThemeSnapshot.value = persistedTheme" in source
    assert '@click="saveTheme"' not in source


def test_theme_preview_status_explains_confirmed_exit_save_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'settings.theme.previewStatus'") == 2
    assert "退出时确认后保存" in source
    assert "saved after confirming exit" in source
    assert "是否保存主题修改并退出主题设置？" in source
    assert "Save theme changes and exit theme settings?" in source


def test_theme_save_reports_success_and_failure_without_losing_dirty_state():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "notifyToast(t('settings.saved'), 'success')" in source
    assert "notifyToast(t('settings.saveFailed'), 'error')" in source
    assert "savedThemeSnapshot.value = persistedTheme" in source


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


def test_theme_snapshot_tracks_external_workspace_changes():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "source !== 'settings' && source !== 'archive'" in source
    assert "void appStore.refreshWorkspaceData().then(() =>" in source
    assert "const externalTheme = cloneTheme(appStore.config.theme)" in source
    assert "savedThemeSnapshot.value = externalTheme" in source
    assert "syncThemeDraft(externalTheme)" in source
    assert "stopWorkspaceListener()" in source


def test_theme_save_has_no_background_refresh_race_or_timer():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "themeSaveInFlight" not in source
    assert "themeSaveTimer" not in source
    assert "themeSavePromise" not in source
    assert "queueThemeSave" not in source


def test_theme_exit_builds_persistence_payload_from_detached_draft():
    source = SETTINGS.read_text(encoding="utf-8")
    save_block = source.split("async function saveTheme", 1)[1].split("async function confirmThemeExit", 1)[0]
    assert "const draftTheme = cloneTheme(buildDraftTheme())" in save_block
    assert "theme: draftTheme" in save_block
    assert "theme: buildDraftTheme()" not in save_block


def test_generic_config_watcher_does_not_overwrite_theme_draft():
    source = SETTINGS.read_text(encoding="utf-8")
    config_watch = source.split("watch(() => config.value,", 1)[1].split("watch(() => config.value.theme", 1)[0]
    assert "overtimeThreshold.value = newConfig.overtime_threshold" in config_watch
    assert "showAmPm.value = newConfig.show_ampm" in config_watch
    assert "themeType.value = newConfig.theme.type" not in config_watch
    assert "syncThemeDraft(newConfig.theme)" not in config_watch
