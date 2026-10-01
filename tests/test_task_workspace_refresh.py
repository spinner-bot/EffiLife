from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_task_center_refreshes_after_unified_workspace_changes():
    source = TASKS.read_text(encoding="utf-8")
    assert "import { notifyWorkspaceChanged, onWorkspaceChanged } from '@/services/workspaceEvents'" in source
    assert "async function refreshFromWorkspace(source?: string): Promise<void>" in source
    assert "['todos', 'records', 'settings', 'archive', 'network'].includes(source)" in source
    assert "await loadTodos()" in source
    assert "await loadCategories()" in source
    assert "stopWorkspaceListener = onWorkspaceChanged" in source
    assert "const pendingWorkspaceSources = new Set<string>()" in source
    assert "async function drainWorkspaceRefresh(): Promise<void>" in source
    assert "pendingWorkspaceSources.add(source)" in source
    assert "stopWorkspaceListener?.()" in source


def test_task_center_does_not_render_storage_failure_as_an_empty_list():
    source = TASKS.read_text(encoding="utf-8")
    assert "const dataUnavailable = ref(false)" in source
    assert "dataUnavailable.value = true" in source
    assert 'class="task-empty task-result-state task-unavailable theme-card" role="status" aria-live="polite"' in source
    assert "@click=\"loadTodos\"" in source
