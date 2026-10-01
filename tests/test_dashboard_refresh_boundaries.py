from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
DAY = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_home_periodic_statistics_refresh_has_error_boundary():
    refresh_block = HOME.split("refreshTimer = window.setInterval(() =>", 1)[1].split("}, 60000)", 1)[0]
    assert "void refreshWorkspaceSummaries()" in refresh_block
    assert "async function refreshWorkspaceSummaries(): Promise<void>" in HOME
    assert "async function refreshTimeSummary(): Promise<void>" in HOME
    assert "Failed to refresh home time summary:" in HOME


def test_home_cross_window_summary_refresh_has_error_boundary():
    refresh_block = HOME.split("workspaceRefreshTimer = window.setTimeout(async () =>", 1)[1].split("}, 80)", 1)[0]
    assert "await refreshWorkspaceSummaries()" in refresh_block
    coordinator = HOME.split("async function refreshWorkspaceSummaries(): Promise<void>", 1)[1].split("function scheduleWorkspaceSummaryRefresh", 1)[0]
    assert "await Promise.all([" in coordinator
    assert "catch (error)" in coordinator
    assert "Failed to refresh home workspace summary:" in HOME


def test_day_detail_initial_load_has_error_boundary():
    assert "void retryLoadData()" in DAY
    assert "Failed to load day detail:" in DAY
    assert "notifyToast(t('dayDetail.loadFailed'), 'error')" in DAY
    assert I18N.count("'dayDetail.loadFailed':") == 2
    assert "const loadError = ref(false)" in DAY
    assert "async function retryLoadData(): Promise<void>" in DAY
    assert 'class="load-error" role="status" aria-live="polite"' in DAY
    assert "@click=\"retryLoadData\"" in DAY
    assert I18N.count("'dayDetail.retry':") == 2
