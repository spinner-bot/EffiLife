from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_date_display_uses_current_locale_and_includes_day():
    source = PLANS.read_text(encoding="utf-8")
    assert "const { t, locale } = useI18n()" in source
    assert "new Intl.DateTimeFormat(locale.value" in source
    assert "year: 'numeric'" in source
    assert "month: '2-digit'" in source
    assert "day: '2-digit'" in source
    assert "return `${year}/${String(month)" not in source
