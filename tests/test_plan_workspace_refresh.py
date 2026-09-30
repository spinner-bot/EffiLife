from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_center_refreshes_external_plan_state_without_racing_local_saves():
    source = PLANS.read_text(encoding="utf-8")
    assert "if (isLoading.value) return" in source
    assert "async function refreshFromWorkspace(source?: string): Promise<void>" in source
    assert "if (selectedPlan.value && (source === 'plans' || source === 'archive'))" in source
    assert "selectedPlan.value = await getPlanFull(selectedPlan.value.id)" in source
    assert "if (view.value === 'events') await loadPlans()" in source
    assert "void refreshFromWorkspace(source).catch" in source
