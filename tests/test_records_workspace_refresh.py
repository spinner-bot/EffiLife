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

