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
        assert "const requestedRecord = records.value[index]" in source
        assert "const resolvedIndex = requestedRecord?.id" in source
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
    assert "const requestedRecord = records.value[index]" in source
    assert "const resolvedIndex = requestedRecord?.id" in source
    assert "await unlinkTodoFromTimeRecord(record)" in source
    assert "import { notifyWorkspaceChanged } from '@/services/workspaceEvents'" in source
    assert "notifyWorkspaceChanged('records')" in source


def test_time_record_actions_have_accessible_names_and_button_types():
    records = RECORDS.read_text(encoding="utf-8")
    day = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert 'type="button" class="icon-btn" :aria-label="t(\'records.edit\')"' in records
    assert 'type="button" class="icon-btn danger" :aria-label="t(\'records.delete\')"' in records
    assert 'type="button" class="delete-btn" :aria-label="t(\'dayDetail.delete\')"' in day
    assert 'type="button" class="close-btn" :aria-label="t(\'dayDetail.close\')"' in day
    assert i18n.count("'dayDetail.delete':") == 2
    assert i18n.count("'dayDetail.close':") == 2


def test_record_save_confirms_success_in_both_locales():
    source = RECORDS.read_text(encoding="utf-8")
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    assert "todoLinkFailed ? t('records.todoLinkFailed') : t('records.saved')" in source
    assert i18n.count("'records.saved':") == 2
