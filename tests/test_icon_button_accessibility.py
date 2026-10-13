from pathlib import Path


ROOT = Path(__file__).parents[1]
EVENTS = (ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue").read_text(encoding="utf-8")
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_event_center_icon_actions_have_screen_reader_names():
    assert 'class="delete-btn" :aria-label="t(\'settings.events.delete\')"' in EVENTS
    assert EVENTS.count(':aria-label="t(\'settings.events.test\')"') >= 2


def test_feedback_copy_action_has_a_dynamic_screen_reader_name():
    assert ':aria-label="copySuccess ? t(\'settings.feedback.copied\') : t(\'settings.feedback.copyEmail\')"' in SETTINGS
