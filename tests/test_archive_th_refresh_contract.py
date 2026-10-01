from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAY_DETAIL = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_th_history_reloads_after_archive_import():
    assert "if (source === 'records' || source === 'plans' || source === 'archive' || source === 'network') void retryLoadData()" in DAY_DETAIL
