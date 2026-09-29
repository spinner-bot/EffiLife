from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
PLAN = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_primary_navigation_no_longer_splits_time_records_from_plans():
    assert 'data-guide="records"' not in APP
    assert 'to="/records"' not in APP


def test_plan_workspace_keeps_history_as_a_secondary_entry():
    assert "legacyPlan.historyRecords" in PLAN
    assert "legacyPlan.historyRecordsDescription" in PLAN
    assert "router.push('/records')" in PLAN
