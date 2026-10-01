from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_time_records_do_not_navigate_into_plan_task_links():
    assert "listPlanArchives" not in VIEW
    assert "listPlanSummaries" not in VIEW
    assert "openLinkedPlan" not in VIEW
