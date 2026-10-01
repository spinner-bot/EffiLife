from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
DAY_DETAIL = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_td_time_tracking_broadcasts_th_record_changes():
    tracking_block = TASKS.split("async function persistTodoTime", 1)[1].split("function formatDeadline", 1)[0]
    assert "await DataService.saveRecord" in tracking_block
    assert "notifyWorkspaceChanged('records')" in tracking_block


def test_th_history_refreshes_when_records_or_plans_change():
    assert "if (source === 'records' || source === 'plans' || source === 'archive' || source === 'network') void retryLoadData()" in DAY_DETAIL
