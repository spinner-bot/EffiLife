from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts"
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_gateway_falls_back_to_snapshot_for_reading():
    source = GATEWAY.read_text(encoding="utf-8")
    assert "export const planDataSource = ref<PlanDataSource>('unknown')" in source
    assert "planDataSource.value = 'cache'" in source
    assert "getMobileRawPlans()" in source
    assert "async function getPlanFull" in source


def test_cached_plan_snapshot_is_read_only_in_desktop_ui():
    plans = PLANS.read_text(encoding="utf-8")
    tasks = TASKS.read_text(encoding="utf-8")
    assert "const canEditPlan = computed(() => isMobilePlanRuntime || planDataSource.value !== 'cache')" in plans
    assert "planDataSource === 'cache'" in plans
    assert "plans-list-source-note" in plans
    assert "@click=\"retryPlanService\"" in plans
    assert "planGatewayState" not in tasks
    assert "retryPlanGateway" not in tasks


def test_cached_plan_mode_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'plans.cachedTitle':") == 2
    assert source.count("'plans.cachedDescription':") == 2
    assert source.count("'tasks.retryPlanService':") == 2


def test_task_center_does_not_expose_plan_linking_controls():
    tasks = TASKS.read_text(encoding="utf-8")
    i18n = I18N.read_text(encoding="utf-8")
    assert "listPlanArchives" not in tasks
    assert "archivedPlanById" not in tasks
    assert "tasks.archivedPlan" not in tasks
