from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_task_center_refreshes_after_unified_workspace_changes():
    source = TASKS.read_text(encoding="utf-8")
    assert "import { onWorkspaceChanged } from '@/services/workspaceEvents'" in source
    assert "async function refreshFromWorkspace(source?: string): Promise<void>" in source
    assert "['todos', 'plans', 'records', 'archive', 'settings'].includes(source)" in source
    assert "await loadTodos()" in source
    assert "await loadCategories()" in source
    assert "stopWorkspaceListener = onWorkspaceChanged" in source
    assert "stopWorkspaceListener?.()" in source
