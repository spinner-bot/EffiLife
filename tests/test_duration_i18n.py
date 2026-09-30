from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DATA = (ROOT / "time-helper/desk/src/services/dataService.ts").read_text(encoding="utf-8")


def test_duration_formatter_has_localized_branches_and_legacy_default():
    assert "export function hoursToHm(totalHours: number, locale = 'zh-CN')" in DATA
    assert "return isEnglish ? '0m' : '0分钟'" in DATA
    assert "return h > 0 ? `${h}h ${m}m` : `${m}m`" in DATA
    assert "return h > 0 ? `${h}小时${m}分钟` : `${m}分钟`" in DATA


def test_visible_duration_call_sites_forward_current_locale():
    for name in ("HomeView.vue", "DayDetailView.vue", "RecordsView.vue", "PlanView.vue"):
        source = (ROOT / "time-helper/desk/src/views" / name).read_text(encoding="utf-8")
        assert "const { t, locale } = useI18n()" in source
        calls = re.findall(r"hoursToHm\([^\n]+\)", source)
        assert calls and all("locale" in call for call in calls), (name, calls)


def test_legacy_plan_hour_unit_is_localized():
    source = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")
    catalog = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")
    assert source.count("t('legacyPlan.hourUnit')") >= 4
    assert "legacyPlan.balanceConfirm', { total, unit: t('legacyPlan.hourUnit') }" in source
    assert catalog.count("'legacyPlan.balanceConfirm':") == 2
    assert "{unit}" in catalog
