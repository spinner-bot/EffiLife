from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_records_page_exposes_a_direct_history_date_entry():
    assert "const historyDate = ref(getTodayDate())" in RECORDS
    assert "router.push(`/day/${historyDate.value}`)" in RECORDS
    assert 'v-model="historyDate"' in RECORDS
    assert 'type="date"' in RECORDS


def test_history_entry_is_bilingual_and_keeps_calendar_out_of_navigation():
    assert I18N.count("'records.historyDate'") == 2
    assert I18N.count("'records.openHistory'") == 2
    assert "calendar" not in RECORDS.lower()
