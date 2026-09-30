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
    assert "async function changeTodayPlan(planName: string)" in source
    assert "await DataService.saveDayPlan(planName, today)" in source
    assert "notifyWorkspaceChanged('plans')" in source.split("async function changeTodayPlan", 1)[1]
    assert "refreshWorkspaceData," in source


def test_workspace_refreshes_are_serialized_and_later_requests_are_not_dropped():
    source = STORE.read_text(encoding="utf-8")
    refresh_block = source.split("async function refreshWorkspaceData()", 1)[1].split("// 保存配置", 1)[0]
    assert "let refreshPromise: Promise<void> | null = null" in source
    assert "let refreshRequested = false" in source
    assert "if (refreshPromise) return refreshPromise" in refresh_block
    assert "do {" in refresh_block
    assert "} while (refreshRequested)" in refresh_block
    assert "if (refreshPromise === currentRefresh) refreshPromise = null" in refresh_block
