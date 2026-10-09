from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_mutations_do_not_share_todo_lifecycle():
    assert "completeLinkedTodos" not in SOURCE
    assert "syncTodosFromPlanTask" not in SOURCE
    assert "syncTodoDescriptionsFromPlan" not in SOURCE


def test_plan_reference_failures_remain_available_for_explicit_link_cleanup():
    assert "todoSyncFailed" in SOURCE
