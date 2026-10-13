from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_legacy_plan_route_redirects_to_time_workspace():
    source = (DESK / "router" / "index.ts").read_text(encoding="utf-8")
    assert "redirect: '/time'" in source


def test_plan_workspace_keeps_event_plans_independent_from_daily_time_workspace():
    source = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "defineAsyncComponent" not in source
    assert "import('@/views/PlanView.vue')" not in source
    assert "view.value = 'time'" not in source
    assert "<DailyPlanView" not in source
    assert "view === 'events'" in source


def test_home_daily_plan_link_uses_dedicated_time_workspace():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    assert 'class="stats-header-row stats-header-action"' in source
    assert 'type="button"' in source
    assert '@click="openDailyPlan"' in source
    assert "router.push('/time')" in source


def test_home_todo_completion_stays_in_the_todo_module():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    todo_completion = source[source.index("async function completeHomeTodo"):source.index("async function addQuickTodo")]
    assert "completePlanTask" not in todo_completion
    assert "await completeTodoWithPlan(todo)" in todo_completion
    focus_bridge = source[source.index("async function startFocusPlan"):source.index("async function refreshTodoSummary")]
    assert "getOrCreatePlanTaskTodo(item.planId, item.task.internal_id" in focus_bridge


def test_home_plan_focus_completion_stays_in_the_ph_gateway():
    source = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
    focus_completion = source[source.index("async function completeHomePlanTask"):source.index("/** Serialize dashboard reads")]
    assert "await completePlanTask(item.planId, item.task.internal_id)" in focus_completion
    assert "TodoService.create" not in focus_completion
