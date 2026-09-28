from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_logs_do_not_render_unknown_time_marker_as_clock_time():
    source = PLANS.read_text(encoding="utf-8")
    assert "function formatLogTime(time?: [number, number]): string" in source
    assert "time[0] === 99 || time[1] === 99" in source
    assert "return t('plans.timeUnknown')" in source
    assert "{{ formatLogTime(log.time) }}" in source
    assert "log.time?.[0] ?? '--'" not in source


def test_plan_log_unknown_time_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert "'plans.timeUnknown': '时间未记录'" in source
    assert "'plans.timeUnknown': 'Time not recorded'" in source

