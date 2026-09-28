from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_unified_shell_exposes_the_time_helper_calendar_route():
    assert "to=\"/calendar\"" in APP
    assert "route.path.startsWith('/calendar')" in APP
    assert "t('nav.calendar')" in APP
