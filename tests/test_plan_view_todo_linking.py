from pathlib import Path


ROOT = Path(__file__).parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")


def test_primary_time_entry_exposes_unified_todo_linking():
    assert "TodoService, type UnifiedTodo" in VIEW
    assert "const selectedTodoId = ref('')" in VIEW
    assert "v-model=\"selectedTodoId\"" in VIEW
    assert "t('records.linkTodo')" in VIEW
    assert "t('records.noLinkedTodo')" in VIEW


def test_primary_time_entry_keeps_todo_time_totals_in_sync_when_saved():
    assert "id: originalRecord?.id || `TR-" in VIEW
    assert "todo_id: selectedTodoId.value || undefined" in VIEW
    assert "TodoService.trackTime(todo.id, recordMinutes, recordId)" in VIEW
    assert "TodoService.adjustTrackedTime(todo.id, recordMinutes - Math.max(1, Math.round(originalRecord.duration * 60)))" in VIEW
    assert "unlinkTodoFromTimeRecord({ ...record, todo_id: originalRecord.todo_id })" in VIEW


def test_primary_time_entry_refreshes_todo_options_after_workspace_changes():
    assert "onWorkspaceChanged" in VIEW
    assert "source === 'todos' || source === 'archive'" in VIEW
    assert "onUnmounted" in VIEW


def test_primary_time_entry_prevents_duplicate_saves_and_surfaces_storage_failures():
    assert "const isSavingRecord = ref(false)" in VIEW
    assert "if (isSavingRecord.value) return" in VIEW
    assert "await saveRecordInternal()" in VIEW
    assert "t('legacyPlan.saveFailed')" in VIEW
    assert ':disabled="isSavingRecord"' in VIEW
