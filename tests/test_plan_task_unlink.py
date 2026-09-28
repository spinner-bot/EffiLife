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
