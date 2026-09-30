from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_custom_settings_uses_native_submit_and_explicit_button_types():
    form = VIEW.split('<form class="custom-settings-form"', 1)[1].split('</form>', 1)[0]

    assert '@submit.prevent="saveCustomSettings"' in form
    assert '<button type="submit" class="btn primary"' in form
    assert '<button type="button" class="threshold-btn"' in form
    assert '<button type="button" class="btn secondary"' in form
    assert '@click="saveCustomSettings"' not in form


def test_custom_settings_save_has_a_recoverable_error_boundary():
    save_block = VIEW.split("async function saveCustomSettings()", 1)[1].split("function addThreshold", 1)[0]
    assert "try {" in save_block
    assert "appStore.saveConfig(newConfig)" in save_block
    assert "settings.saveFailed" in save_block


def test_external_config_refresh_preserves_unsaved_custom_settings_draft():
    assert "type CustomSettingsDraft = Pick<Config" in VIEW
    assert "const savedCustomSettingsSnapshot = ref<CustomSettingsDraft>" in VIEW
    assert "const customSettingsDirty = computed" in VIEW
    assert "const hadLocalDraft = customSettingsDirty.value" in VIEW
    assert "if (!hadLocalDraft)" in VIEW
    assert "savedCustomSettingsSnapshot.value = currentCustomSettings()" in VIEW
