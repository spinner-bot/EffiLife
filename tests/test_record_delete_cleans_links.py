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
