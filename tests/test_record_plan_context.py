from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"


def test_time_records_expose_read_only_plan_context_through_linked_todo():
    source = RECORDS.read_text(encoding="utf-8")
    assert "todoPlanReferenceById" in source
    assert "todo.related_plan_id && todo.related_plan_task_id" in source
    assert "class=\"record-plan-reference\"" in source
    assert "PH {{ todoPlanReferenceById.get(record.todo_id) }}" in source

