from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_custom_bgm_control_does_not_nest_interactive_roles():
    source = (ROOT / "time-helper/desk/src/views/AudioSettingsView.vue").read_text(encoding="utf-8")

    assert 'role="button" tabindex="0"' not in source
    assert 'class="bgm-select"' in source
    assert ':aria-pressed="audioSettings.currentBgm === bgm.id"' in source
    assert '@click.stop="removeCustomBgm' not in source


def test_custom_bgm_remove_action_remains_a_button():
    source = (ROOT / "time-helper/desk/src/views/AudioSettingsView.vue").read_text(encoding="utf-8")

    assert 'class="remove-btn" type="button"' in source
