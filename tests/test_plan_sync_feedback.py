from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_completion_reports_linked_todo_synchronization_failures():
    assert "todoSyncFailed" in SOURCE
    assert "completeLinkedTodos" in SOURCE
    assert "syncTodoDescriptionsFromPlan" not in SOURCE
