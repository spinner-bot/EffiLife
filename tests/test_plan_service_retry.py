from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_cached_plan_detail_can_retry_the_live_service():
    source = PLANS.read_text(encoding="utf-8")
    assert "async function retryPlanService()" in source
    assert "selectedPlan.value = await getPlanFull(selectedPlan.value.id)" in source
    assert "@click=\"retryPlanService\"" in source
    assert "plans-retry" in source


def test_retry_copy_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.retryService':") == 2
