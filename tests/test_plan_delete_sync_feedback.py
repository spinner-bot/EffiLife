from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_single_plan_task_delete_reports_the_plan_mutation_directly():
    delete_block = VIEW.split("async function deleteTask", 1)[1].split("function backFromDetail", 1)[0]
    assert "todoSyncFailed" not in delete_block
    assert "unlinkTodosFromPlanTask" not in delete_block
    assert "\n    showPlanSaved()" in delete_block
