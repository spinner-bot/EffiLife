from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_task_duration_uses_localized_unit():
    source = PLANS.read_text(encoding="utf-8")
    assert "t('plans.minutesShort')" in source
    assert "{{ task.time_minutes }} min" not in source


def test_plan_duration_unit_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.minutesShort'") == 2
