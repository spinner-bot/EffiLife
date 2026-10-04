from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
STORE = ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts"


def test_app_shell_refreshes_shared_state_after_cross_window_changes():
    source = APP.read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "appStore.refreshWorkspaceData()" in source
    assert "['plans', 'records', 'settings', 'archive', 'network']" in source
    assert "stopWorkspaceListener?.()" in source
    assert "document.addEventListener('visibilitychange', refreshWhenVisible)" in source
    assert "document.removeEventListener('visibilitychange', refreshWhenVisible)" in source
    assert "refreshLocaleFromStorage()" in source
    assert "if (source === 'settings')" in source
    assert "if (source === 'archive')" in source
    assert "refreshLocaleFromStorage()" in source


def test_workspace_events_distinguish_same_window_and_remote_changes():
    events = (ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts").read_text(encoding="utf-8")
    assert "WORKSPACE_ORIGIN" in events
    assert "origin: WORKSPACE_ORIGIN" in events
    assert "listener(message?.source, false)" in events
    assert "event.data?.origin !== WORKSPACE_ORIGIN" in events


def test_workspace_events_fall_back_to_storage_for_cross_window_locale_sync():
    events = (ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts").read_text(encoding="utf-8")
    assert "const LOCALE_STORAGE_KEY = 'efflife_locale'" in events
    assert "window.addEventListener('storage', storageHandler)" in events
    assert "if (event.key === LOCALE_STORAGE_KEY) listener('settings', true)" in events
    assert "window.removeEventListener('storage', storageHandler)" in events


def test_workspace_refresh_discards_reads_started_before_local_config_write():
    source = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")
    assert "let workspaceWriteVersion = 0" in source
    assert "const readVersion = workspaceWriteVersion" in source
    assert "if (readVersion !== workspaceWriteVersion)" in source
    assert "refreshRequested = true" in source
    assert "workspaceWriteVersion += 1" in source


def test_workspace_refresh_preserves_successful_datasets_when_one_read_fails():
    source = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")
    refresh_block = source.split("async function refreshWorkspaceData()", 1)[1].split("// 保存配置", 1)[0]
    assert "const workspaceResults = await Promise.allSettled([" in refresh_block
    assert "if (configResult.status === 'fulfilled') config.value = configResult.value" in refresh_block
    assert "if (recordsResult.status === 'fulfilled') todayRecords.value = recordsResult.value" in refresh_block
    assert "preserved their previous values" in refresh_block
    assert "failedReads.length === workspaceResults.length" in refresh_block


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
