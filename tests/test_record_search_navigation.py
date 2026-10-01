from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_record_deep_links_scroll_to_the_highlighted_history_entry():
    assert "function recordDomId(record: TimeRecord, index: number)" in VIEW
    assert "recordKey(record, index).replace(/[^a-zA-Z0-9_-]/g, '-')" in VIEW
    assert "scrollIntoView({ behavior: 'smooth', block: 'center' })" in VIEW
    assert ':id="recordDomId(record, index)"' in VIEW
    assert "watch(highlightedRecordKey" in VIEW

