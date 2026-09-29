from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO_VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "AudioSettingsView.vue"


def test_custom_audio_item_does_not_nest_interactive_buttons():
    source = AUDIO_VIEW.read_text(encoding="utf-8")

    assert 'role="button" tabindex="0"' in source
    assert '@keydown="selectBgmFromKeyboard($event, bgm.id)"' in source
    assert '<button class="remove-btn" @click.stop="removeCustomBgm(bgm.id)">' in source
    assert 'function selectBgmFromKeyboard(event: KeyboardEvent, bgmId: string)' in source


def test_custom_audio_keyboard_selection_preserves_enter_and_space_support():
    source = AUDIO_VIEW.read_text(encoding="utf-8")

    assert "event.key !== 'Enter' && event.key !== ' '" in source
    assert "event.preventDefault()" in source
    assert "selectBgm(bgmId)" in source
