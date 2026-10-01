from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_operations_do_not_perform_todo_synchronization():
    assert "todoSyncFailed" not in SOURCE
    assert "syncTodosFromPlanTask" not in SOURCE
    assert "syncTodoDescriptionsFromPlan" not in SOURCE
    assert "completeLinkedTodos" not in SOURCE
