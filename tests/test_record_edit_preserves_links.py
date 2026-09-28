from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"
PLAN = ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue"


def test_records_view_preserves_identity_and_todo_link_on_edit():
    source = RECORDS.read_text(encoding="utf-8")
    assert "const originalRecord = isEditing.value ? records.value[editingIndex.value] : undefined" in source
    assert "id: originalRecord?.id" in source
    assert "todo_id: originalRecord?.todo_id" in source


def test_unified_plan_workspace_preserves_identity_and_todo_link_on_edit():
    source = PLAN.read_text(encoding="utf-8")
    assert "const originalRecord = isEditing.value ? records.value[editingIndex.value] : undefined" in source
    assert "id: originalRecord?.id" in source
    assert "todo_id: originalRecord?.todo_id" in source
