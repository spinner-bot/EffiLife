from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_deleting_a_plan_task_clears_only_its_todo_relation():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "unlinkTodosFromPlanTask(planId: string, planTaskId: string)" in sync
    assert "related_plan_task_id === String(planTaskId)" in sync
    assert "related_plan_id: undefined" in sync
    assert "related_plan_task_id: undefined" in sync
    assert "unlinkTodosFromPlanTask(planId, taskId)" in plans


def test_plan_task_edit_does_not_sync_linked_todo_fields():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodosFromPlanTask" not in sync
    assert "time_estimate: Math.max(0, Number(minutes) || 0)" not in sync
    assert "estimated_time: Math.max(0, Number(minutes) || 0)" not in sync
    assert "editingTaskDisplayId" not in plans
    assert "syncTodosFromPlanTask(planId, editedTaskId, nextContent, minutes)" not in plans


def test_plan_rename_does_not_refresh_todo_descriptions():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodoDescriptionsFromPlan" not in sync
    assert "todo.description === previousName" not in sync
    assert "syncTodoDescriptionsFromPlan(planId, previousName, nextName)" not in plans


def test_plan_completion_has_no_todo_completion_side_effect():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "completeLinkedTodos" not in sync
    assert "completeLinkedTodos" not in plans
