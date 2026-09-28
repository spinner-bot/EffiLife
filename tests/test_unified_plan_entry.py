from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_legacy_plan_route_redirects_to_unified_workspace():
    source = (DESK / "router" / "index.ts").read_text(encoding="utf-8")
    assert "redirect: { path: '/plans', query: { mode: 'time' } }" in source


def test_unified_workspace_embeds_daily_plan_view_and_preserves_event_mode():
    source = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "defineAsyncComponent" in source
    assert "import('@/views/PlanView.vue')" in source
    assert "view.value = 'time'" in source
    assert "<DailyPlanView v-if=\"view === 'time'\" />" in source
    assert "view === 'events'" in source


def test_home_daily_plan_link_uses_unified_workspace_query():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert "function activateDailyPlan" in source
    assert 'role="button"' in source
    assert 'tabindex="0"' in source
    assert "@keydown=\"activateDailyPlan\"" in source
    assert "router.push({ path: '/plans', query: { mode: 'time' } })" in source
