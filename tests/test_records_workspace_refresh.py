from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"


def test_records_view_refreshes_todo_picker_after_workspace_changes():
    source = RECORDS.read_text(encoding="utf-8")
    assert "import { onWorkspaceChanged } from '@/services/workspaceEvents'" in source
    assert "async function loadTodoOptions(): Promise<void>" in source
    assert "if (source === 'todos' || source === 'archive') void loadTodoOptions()" in source
    assert "if (source === 'records' || source === 'plans' || source === 'settings' || source === 'archive')" in source
    assert "void appStore.refreshWorkspaceData().catch" in source
    assert "Failed to refresh records workspace after external change:" in source
    assert "stopWorkspaceListener?.()" in source
    assert "await loadTodoOptions()" in source
    assert "loadPlanContexts" not in source


def test_records_view_does_not_turn_todo_picker_failure_into_an_empty_choice_list():
    source = RECORDS.read_text(encoding="utf-8")
    assert "const todoOptionsUnavailable = ref(false)" in source
    assert "todoOptionsUnavailable.value = true" in source
    assert ':disabled="todoOptionsUnavailable"' in source
    assert 'class="todo-options-unavailable" role="status" aria-live="polite"' in source
    assert "@click=\"loadTodoOptions\"" in source


def test_records_edit_resolves_the_current_record_by_stable_id_after_refresh():
    source = RECORDS.read_text(encoding="utf-8")
    assert "const editingRecordId = ref<string | null>(null)" in source
    assert "editingRecordId.value = record.id || null" in source
    assert "const resolvedEditingIndex = isEditing.value && editingRecordId.value" in source
    assert "records.value.findIndex((item) => item.id === editingRecordId.value)" in source
    assert "appStore.updateRecord(resolvedEditingIndex, record)" in source
    assert "records.validation.recordMissing" in source
