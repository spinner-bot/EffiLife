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


def test_plan_task_edit_syncs_linked_todo_fields_without_editing_plan_from_td():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodosFromPlanTask" in sync
    assert "time_estimate: Math.max(0, Number(minutes) || 0)" in sync
    assert "estimated_time: Math.max(0, Number(minutes) || 0)" in sync
    assert "editingTaskDisplayId" not in plans
    assert "syncTodosFromPlanTask(planId, editedTaskId, nextContent, minutes)" in plans


def test_plan_rename_refreshes_system_generated_todo_descriptions():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodoDescriptionsFromPlan" in sync
    assert "todo.description === previousName" in sync
    assert "syncTodoDescriptionsFromPlan(planId, previousName, nextName)" in plans


def test_plan_completion_does_not_resurrect_archived_or_cancelled_todos():
    sync = SYNC.read_text(encoding="utf-8")
    assert "!['completed', 'archived', 'cancelled'].includes(todo.status)" in sync
