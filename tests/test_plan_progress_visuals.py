from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_cards_and_detail_show_progress_without_dividing_by_zero():
    source = PLANS.read_text(encoding="utf-8")
    assert "function planProgress(plan: PlanSummary)" in source
    assert "total > 0 ? Math.round" in source
    assert "plan-progress-track" in source
    assert "selectedPlanProgress" in source


def test_plan_progress_label_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.progress'") == 2
