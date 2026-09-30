from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
PLAN = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_primary_navigation_exposes_time_records_without_replacing_the_time_workspace():
    assert 'data-guide="records"' in APP
    assert 'to="/records"' in APP
    assert 'to="/time"' in APP


def test_plan_workspace_keeps_history_as_a_secondary_entry():
    assert "legacyPlan.historyRecords" in PLAN
    assert "legacyPlan.historyRecordsDescription" in PLAN
    assert "router.push('/records')" in PLAN
