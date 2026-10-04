from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO_VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "AudioSettingsView.vue"


def test_custom_audio_item_does_not_nest_interactive_buttons():
    source = AUDIO_VIEW.read_text(encoding="utf-8")

    assert 'class="bgm-select"' in source
    assert ':aria-pressed="audioSettings.currentBgm === bgm.id"' in source
    assert 'class="remove-btn" type="button" :aria-label="t(\'settings.audio.removeCustom\')"' in source
    assert 'role="button" tabindex="0"' not in source


def test_custom_audio_keyboard_selection_preserves_enter_and_space_support():
    source = AUDIO_VIEW.read_text(encoding="utf-8")

    assert 'type="button" class="bgm-select"' in source
    assert '@click="selectBgm(bgm.id)"' in source
    assert '@click.stop="removeCustomBgm' not in source


def test_icon_only_audio_controls_have_bilingual_labels():
    source = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    for key in ("settings.audio.testSound", "settings.audio.addCustom", "settings.audio.removeCustom"):
        assert source.count(f"'{key}'") == 2
