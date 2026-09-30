from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "CheckinView.vue").read_text(encoding="utf-8")


def test_checkin_weekdays_use_current_locale_instead_of_hardcoded_prefixes():
    assert "const { t, locale } = useI18n()" in VIEW
    assert "new Intl.DateTimeFormat(locale.value, { weekday: 'short' }).format(d)" in VIEW
    assert "const weekdays = [" not in VIEW
    assert "return `周${weekdays" not in VIEW
