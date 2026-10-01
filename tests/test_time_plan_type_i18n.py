from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
DAY_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_time_plan_type_values_are_localized_only_at_the_display_boundary():
    assert "function planTypeLabel(value?: string): string" in VIEW
    assert "t('legacyPlan.split')" in VIEW
    assert "t('legacyPlan.allocate')" in VIEW
    assert "planTypeLabel(plan.plan_type)" in VIEW
    assert "planTypeLabel(todayPlan.type)" in VIEW
    assert "{{ plan.plan_type }}" not in VIEW


def test_day_detail_localizes_legacy_plan_type_values():
    assert "function planTypeLabel(value?: string): string" in DAY_VIEW
    assert "t('legacyPlan.split')" in DAY_VIEW
    assert "t('legacyPlan.allocate')" in DAY_VIEW
    assert "planTypeLabel(dayPlanType)" in DAY_VIEW
    assert "planTypeLabel(plan.plan_type)" in DAY_VIEW
    assert "{{ dayPlanType }}" not in DAY_VIEW
    assert "{{ plan.plan_type }}" not in DAY_VIEW
