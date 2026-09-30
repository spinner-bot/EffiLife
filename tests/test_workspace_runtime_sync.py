from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
STORE = ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts"


def test_app_shell_refreshes_shared_state_after_cross_window_changes():
    source = APP.read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "appStore.refreshWorkspaceData()" in source
    assert "['plans', 'records', 'settings', 'archive']" in source
    assert "stopWorkspaceListener?.()" in source
    assert "document.addEventListener('visibilitychange', refreshWhenVisible)" in source
    assert "document.removeEventListener('visibilitychange', refreshWhenVisible)" in source
    assert "refreshLocaleFromStorage()" in source
    assert "if (source === 'archive' || source === 'settings') refreshLocaleFromStorage()" in source


def test_app_store_exposes_atomic_workspace_refresh_and_emits_mutation_sources():
    source = STORE.read_text(encoding="utf-8")
    assert "async function refreshWorkspaceData()" in source
    assert "config.value = await DataService.loadConfig()" in source
    assert "plans.value = await DataService.loadPlans()" in source
    assert "notifyWorkspaceChanged('settings')" in source
    assert "notifyWorkspaceChanged('plans')" in source
    assert "refreshWorkspaceData," in source
