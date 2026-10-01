from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_center_refreshes_external_plan_state_without_racing_local_saves():
    source = PLANS.read_text(encoding="utf-8")
    assert "async function refreshFromWorkspace(source?: string): Promise<void>" in source
    assert "if (selectedPlan.value && (source === 'plans' || source === 'archive'))" in source
    assert "selectedPlan.value = await getPlanFull(selectedPlan.value.id)" in source
    assert "if (view.value === 'events') await loadPlans()" in source
    assert "const pendingWorkspaceSources = new Set<string>()" in source
    assert "async function drainWorkspaceRefresh(): Promise<void>" in source
    assert "pendingWorkspaceSources.add(source)" in source
    assert "watch(isLoading, (loading)" in source


def test_plan_center_distinguishes_unavailable_archives_from_an_empty_archive_list():
    source = PLANS.read_text(encoding="utf-8")
    gateway = (ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts").read_text(encoding="utf-8")
    assert "planArchivesState" in gateway
    assert "planArchivesState.value = 'unavailable'" in gateway
    assert "const archivesUnavailable = computed" in source
    assert 'class="section-empty archive-unavailable" role="status" aria-live="polite"' in source
    assert "plans.retryArchives" in source
