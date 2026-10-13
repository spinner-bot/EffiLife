from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"
SYNC = (DESK / "services" / "workspaceSync.ts").read_text(encoding="utf-8")
HOME = (DESK / "views" / "HomeView.vue").read_text(encoding="utf-8")
PLANS = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_completion_projects_to_exact_active_todo_relations():
    assert "export async function completeLinkedPlanTodo" in SYNC
    assert "todo.related_plan_id === String(planId)" in SYNC
    assert "todo.related_plan_task_id === String(planTaskId)" in SYNC
    assert "todo.status !== 'completed'" in SYNC
    assert "todo.status !== 'archived'" in SYNC
    assert "todo.status !== 'cancelled'" in SYNC
    assert "await TodoService.complete(todo.id)" in SYNC


def test_plan_workspaces_keep_ph_success_when_td_projection_fails():
    for source in (HOME, PLANS):
        completion = source[source.index("await completePlanTask"):source.index("notifyToast(t('plans.todoSyncFailed')", source.index("await completePlanTask"))]
        assert "await completeLinkedPlanTodo" in completion
        assert "try" in completion

