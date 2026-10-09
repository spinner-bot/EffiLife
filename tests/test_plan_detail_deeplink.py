from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_detail_syncs_query_and_preserves_task_deep_links():
    source = PLANS.read_text(encoding="utf-8")

    assert "query: { ...route.query, plan: String(plan.id) }" in source
    assert "query: { plan: String(createdId) }" in source
    assert "router.replace({ path: '/plans', query: {} })" in source


def test_stale_task_deep_link_explains_missing_target_without_hiding_plan():
    source = PLANS.read_text(encoding="utf-8")

    assert "const missingTaskTargetId = ref<string | null>(null)" in source
    assert "missingTaskTargetId.value = taskId" in source
    assert "class=\"plans-readonly-note task-target-missing\"" in source
    assert "plans.taskTargetMissing" in source
