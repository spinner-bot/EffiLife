from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"
PLAN = ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue"


def test_workspace_sync_removes_deleted_record_id_only():
    source = SYNC.read_text(encoding="utf-8")
    assert "unlinkTodoFromTimeRecord(record: TimeRecord)" in source
    assert "related_time_record_ids.filter((id) => id !== record.id)" in source


def test_record_delete_paths_clean_linked_todo_references():
    for source_path in (RECORDS, PLAN):
        source = source_path.read_text(encoding="utf-8")
        assert "const record = records.value[index]" in source
        assert "await unlinkTodoFromTimeRecord(record)" in source


def test_deleted_todo_unlinks_time_records_without_deleting_history():
    data = (ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts").read_text(encoding="utf-8")
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")

    assert "async unlinkTodoFromRecords(todoId: string): Promise<number>" in data
    assert "delete nextRecord.todo_id" in data
    assert "await DataService.unlinkTodoFromRecords(todo.id)" in tasks


def test_day_detail_delete_cleans_linked_todo_reference():
    source = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")

    assert "import { unlinkTodoFromTimeRecord } from '@/services/workspaceSync'" in source
    assert "const record = records.value[index]" in source
    assert "await unlinkTodoFromTimeRecord(record)" in source
