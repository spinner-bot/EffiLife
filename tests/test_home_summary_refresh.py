from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"


def test_home_refreshes_workspace_summaries_periodically():
    source = HOME.read_text(encoding="utf-8")
    assert "refreshTimer = window.setInterval(() => { void refreshWorkspaceSummaries() }, 60000)" in source
    assert "Keep the dashboard summaries fresh even when no workspace event is emitted." in source


def test_home_clears_periodic_summary_refresh_on_unmount():
    source = HOME.read_text(encoding="utf-8")
    assert "if (refreshTimer) clearInterval(refreshTimer)" in source
