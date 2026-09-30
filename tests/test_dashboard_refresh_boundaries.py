from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
DAY = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_home_periodic_statistics_refresh_has_error_boundary():
    refresh_block = HOME.split("refreshTimer = window.setInterval(() =>", 1)[1].split("}, 60000)", 1)[0]
    assert "void appStore.refreshTodayData().catch((error) =>" in refresh_block
    assert "Failed to refresh home statistics:" in refresh_block


def test_home_cross_window_summary_refresh_has_error_boundary():
    refresh_block = HOME.split("workspaceRefreshTimer = window.setTimeout(async () =>", 1)[1].split("}, 80)", 1)[0]
    assert "await Promise.all([" in refresh_block
    assert "catch (error)" in refresh_block
    assert "Failed to refresh home workspace summary:" in refresh_block


def test_day_detail_initial_load_has_error_boundary():
    assert "void loadData().catch((error) =>" in DAY
    assert "Failed to load day detail:" in DAY
    assert "notifyToast(t('dayDetail.loadFailed'), 'error')" in DAY
    assert I18N.count("'dayDetail.loadFailed':") == 2
