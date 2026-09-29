from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_detail_syncs_query_and_preserves_task_deep_links():
    source = PLANS.read_text(encoding="utf-8")

    assert "query: { ...route.query, plan: String(plan.id) }" in source
    assert "query: { plan: String(createdId) }" in source
    assert "createEventPlanFromTemplate" in source
    assert "router.replace({ path: '/plans', query: {} })" in source
