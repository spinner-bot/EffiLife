from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"


def test_records_view_refreshes_todo_picker_after_workspace_changes():
    source = RECORDS.read_text(encoding="utf-8")
    assert "import { onWorkspaceChanged } from '@/services/workspaceEvents'" in source
    assert "async function loadTodoOptions(): Promise<void>" in source
    assert "if (source === 'todos' || source === 'archive') void loadTodoOptions()" in source
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
