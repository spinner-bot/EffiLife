from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_single_plan_task_delete_does_not_show_success_after_todo_cleanup_failure():
    delete_block = VIEW.split("async function deleteTask", 1)[1].split("function backFromDetail", 1)[0]
    assert "let todoSyncFailed = false" in delete_block
    assert "errorMessage.value = t('plans.todoSyncFailed')" in delete_block
    assert "if (!todoSyncFailed) showPlanSaved()" in delete_block
    assert "\n    showPlanSaved()" not in delete_block

