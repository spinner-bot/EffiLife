from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_custom_settings_save_is_serialized_and_releases_busy_state():
    assert "const savingCustomSettings = ref(false)" in VIEW
    save_block = VIEW.split("async function saveCustomSettings()", 1)[1].split("function addThreshold", 1)[0]
    assert "if (savingCustomSettings.value) return" in save_block
    assert "savingCustomSettings.value = true" in save_block
    assert "savingCustomSettings.value = false" in save_block
    assert "finally" in save_block


def test_custom_settings_controls_cannot_change_or_leave_during_save():
    form = VIEW.split('<form class="custom-settings-form"', 1)[1].split('</form>', 1)[0]
    assert form.count(':disabled="savingCustomSettings"') >= 6
