from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIO = (ROOT / "time-helper" / "desk" / "src" / "views" / "AudioSettingsView.vue").read_text(encoding="utf-8")
EVENTS = (ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue").read_text(encoding="utf-8")


def test_audio_sliders_have_visible_programmatic_labels():
    assert 'id="sfx-master-volume-label"' in AUDIO
    assert 'aria-labelledby="sfx-master-volume-label"' in AUDIO
    assert ':aria-labelledby="`sfx-volume-label-${sfx.type}`"' in AUDIO
    assert 'id="bgm-volume-label"' in AUDIO
    assert 'aria-labelledby="bgm-volume-label"' in AUDIO


def test_event_rule_inputs_are_associated_with_visible_labels():
    assert 'for="event-rule-hour"' in EVENTS
    assert 'id="event-rule-hour"' in EVENTS
    assert 'for="event-rule-minute"' in EVENTS
    assert 'id="event-rule-minute"' in EVENTS
    assert 'for="event-rule-threshold"' in EVENTS
    assert 'id="event-rule-threshold"' in EVENTS
