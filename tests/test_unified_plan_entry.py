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


def test_home_daily_plan_link_uses_dedicated_time_workspace():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert 'class="stats-header-row stats-header-action"' in source
    assert 'type="button"' in source
    assert '@click="openDailyPlan"' in source
    assert "router.push('/time')" in source


def test_home_todo_completion_syncs_linked_plan_task_first():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert "import { completePlanTask" in source
    assert "if (todo.related_plan_id && todo.related_plan_task_id)" in source
    assert "await completePlanTask(todo.related_plan_id, todo.related_plan_task_id)" in source
    assert "await TodoService.complete(todo.id)" in source
