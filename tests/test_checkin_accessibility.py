from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKIN = (ROOT / "time-helper" / "desk" / "src" / "views" / "CheckinView.vue").read_text(encoding="utf-8")


def test_disabled_checkin_action_is_explicitly_non_submit_button():
    disabled_action = CHECKIN.split('<button', 3)[3].split('</button>', 1)[0]

    assert 'type="button"' in disabled_action
    assert 'v-else' in disabled_action
    assert 'disabled' in disabled_action
