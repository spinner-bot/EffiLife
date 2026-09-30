from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper" / "desk" / "src"


def test_current_heatmap_ui_does_not_use_retired_calendar_keys():
    checkin = (SRC / "views" / "CheckinView.vue").read_text(encoding="utf-8")
    heatmap = (SRC / "components" / "ContributionHeatmap.vue").read_text(encoding="utf-8")
    assert "checkin.calendar" not in checkin
    assert "calendar.weekday." not in heatmap
    assert "checkin.heatmap" in checkin
    assert "heatmap.weekday." in heatmap


def test_heatmap_terminology_is_bilingual():
    catalog = (SRC / "i18n" / "index.ts").read_text(encoding="utf-8")
    for key in ("checkin.heatmap", "heatmap.weekday.mon", "heatmap.weekday.sun"):
        assert catalog.count(f"'{key}':") == 2
