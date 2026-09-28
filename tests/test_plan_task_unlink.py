from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_deleting_a_plan_task_unlinks_existing_todos():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "unlinkTodosFromPlanTask(planId: string, planTaskId: string)" in sync
    assert "related_plan_task_id === String(planTaskId)" in sync
    assert "related_plan_id: undefined" in sync
    assert "related_plan_task_id: undefined" in sync
    assert "await unlinkTodosFromPlanTask(planId, taskId)" in plans


def test_plan_task_edit_syncs_linked_todo_title_and_duration():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodosFromPlanTask" in sync
    assert "time_estimate: Math.max(0, Number(minutes) || 0)" in sync
    assert "estimated_time: Math.max(0, Number(minutes) || 0)" in sync
    assert "syncTodosFromPlanTask(planId, [editingTaskId.value]" in plans


def test_plan_rename_refreshes_only_system_derived_todo_descriptions():
    sync = SYNC.read_text(encoding="utf-8")
    plans = PLANS.read_text(encoding="utf-8")
    assert "export async function syncTodoDescriptionsFromPlan" in sync
    assert "todo.description === previousName" in sync
    assert "syncTodoDescriptionsFromPlan(planId, previousName, planName.value.trim())" in plans
