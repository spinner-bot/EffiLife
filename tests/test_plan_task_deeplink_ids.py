from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_task_deep_links_resolve_internal_and_display_ids_to_internal_dom_ids():
    assert ".find((item) => item.internal_id === taskId || item.display_id === taskId)" in VIEW
    assert "const internalTaskId = task.internal_id" in VIEW
    assert "searchTargetTaskId.value = internalTaskId" in VIEW
    assert "plan-task-${internalTaskId}" in VIEW
