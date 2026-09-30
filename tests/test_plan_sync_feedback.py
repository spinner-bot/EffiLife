from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_operations_do_not_claim_full_sync_after_todo_sync_failure():
    assert SOURCE.count("let todoSyncFailed = false") == 4
    assert SOURCE.count("if (!todoSyncFailed) showPlanSaved()") == 4
    assert SOURCE.count("todoSyncFailed = true") == 4
