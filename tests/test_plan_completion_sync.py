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
    assert "let firstError: unknown = null" in SYNC
    assert "firstError ??= error" in SYNC
    assert "if (firstError) throw firstError" in SYNC


def test_plan_workspaces_keep_ph_success_when_td_projection_fails():
    for source in (HOME, PLANS):
        completion = source[source.index("await completePlanTask"):source.index("notifyToast(t('plans.todoSyncFailed')", source.index("await completePlanTask"))]
        assert "await completeLinkedPlanTodo" in completion
        assert "try" in completion


def test_td_completion_uses_the_ph_first_coordinator():
    assert "export async function completeTodoWithPlan" in SYNC
    assert "await completePlanTask(todo.related_plan_id, todo.related_plan_task_id)" in SYNC
    assert "return await TodoService.complete(todo.id)" in SYNC
    assert "await completeTodoWithPlan(todo)" in HOME
    assert "await completeTodoWithPlan(todo)" in (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_td_projection_failure_has_a_distinct_recoverable_error_path():
    assert "export class PlanTodoSyncError extends Error" in SYNC
    assert "throw new PlanTodoSyncError(error)" in SYNC
    assert "error instanceof PlanTodoSyncError" in HOME
    assert "error instanceof PlanTodoSyncError" in (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_single_todo_completion_has_success_feedback():
    tasks = (DESK / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    catalog = (DESK / "i18n" / "index.ts").read_text(encoding="utf-8")
    completion = tasks[tasks.index("async function completeTodo"):tasks.index("function startEdit")]
    assert "notifyToast(t('tasks.completedOne'), 'success')" in completion
    home = HOME[HOME.index("async function completeHomeTodo"):HOME.index("async function addQuickTodo")]
    assert "notifyToast(t('tasks.completedOne'), 'success')" in home
    assert catalog.count("'tasks.completedOne':") == 2

