from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_manual_record_form_can_link_a_unified_todo():
    source = RECORDS.read_text(encoding="utf-8")
    assert "TodoService.list()" in source
    assert "selectedTodoId" in source
    assert "todo_id: selectedTodoId.value || undefined" in source
    assert "related_time_record_ids" in source
    assert "records.linkTodo" in source


def test_record_edit_reconciles_previous_todo_link():
    source = RECORDS.read_text(encoding="utf-8")
    assert "originalRecord?.todo_id && originalRecord.todo_id !== record.todo_id" in source
    assert "unlinkTodoFromTimeRecord({ ...record, todo_id: originalRecord.todo_id })" in source
    assert "records.todoLinkFailed" in source


def test_record_todo_link_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("records.linkTodo", "records.noLinkedTodo", "records.linkedTodo", "records.todoLinkFailed"):
        assert source.count(f"'{key}':") == 2
