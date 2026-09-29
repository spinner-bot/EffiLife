from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / "time-helper" / "desk" / "src" / "audio" / "AudioManager.ts"


def test_removing_active_custom_bgm_returns_to_declared_default_source():
    source = AUDIO.read_text(encoding="utf-8")

    assert "if (this.settings.value.currentBgm === id)" in source
    assert "this.settings.value.currentBgm = DEFAULT_AUDIO_SETTINGS.currentBgm" in source
    assert "this.settings.value.currentBgm = 'default'" not in source
    assert "this.updateBgm()" in source
