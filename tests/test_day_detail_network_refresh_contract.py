from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAY_DETAIL = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_historical_day_detail_refreshes_after_network_recovery():
    assert "if (source === 'network') void retryLoadData()" in DAY_DETAIL
    assert "async function retryLoadData(): Promise<void>" in DAY_DETAIL
