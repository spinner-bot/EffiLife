from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reusable_non_form_buttons_declare_an_explicit_button_type():
    sources = {
        "audio": (ROOT / "time-helper/desk/src/views/AudioSettingsView.vue").read_text(encoding="utf-8"),
        "checkin": (ROOT / "time-helper/desk/src/data/CheckinPopup.vue").read_text(encoding="utf-8"),
        "guide": (ROOT / "time-helper/desk/src/guide/GuideOverlay.vue").read_text(encoding="utf-8"),
    }
    assert '<button type="button" class="tab-btn active">' in sources["audio"]
    assert '<button type="button" v-if="phase === \'done\'"' in sources["checkin"]
    assert '<button type="button" class="checkin-btn"' in sources["checkin"]
    assert sources["guide"].count('<button type="button"') >= 3
