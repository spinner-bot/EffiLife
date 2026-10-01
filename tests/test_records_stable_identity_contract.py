from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_records_list_prefers_stable_record_identity_over_array_index():
    assert "function recordKey(record: TimeRecord, index: number): string" in RECORDS
    assert "return record.id || `${record.date || getTodayDate()}-${record.start}-${record.end}-${index}`" in RECORDS
    assert ':key="recordKey(record, index)"' in RECORDS
