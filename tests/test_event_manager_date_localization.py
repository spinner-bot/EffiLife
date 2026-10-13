from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue"


def test_event_inbox_time_uses_current_locale_and_date_time_parts():
    source = SOURCE.read_text(encoding="utf-8")

    assert "const { t, locale } = useI18n()" in source
    block = source.split("function formatTriggerTime", 1)[1].split("function getEventStyle", 1)[0]
    assert "new Intl.DateTimeFormat(locale.value" in block
    assert "month: '2-digit'" in block
    assert "day: '2-digit'" in block
    assert "hour: '2-digit'" in block
    assert "minute: '2-digit'" in block
    assert "if (Number.isNaN(d.getTime())) return entry.triggeredAt" in block


def test_event_manager_does_not_rebuild_trigger_time_with_fixed_month_day_string():
    source = SOURCE.read_text(encoding="utf-8")
    block = source.split("function formatTriggerTime", 1)[1].split("function getEventStyle", 1)[0]

    assert "return `${month}-${day} ${hour}:${minute}`" not in block
