from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = (ROOT / "time-helper/desk/src/views/RecordsView.vue").read_text(encoding="utf-8")
DAY = (ROOT / "time-helper/desk/src/views/DayDetailView.vue").read_text(encoding="utf-8")


def test_today_record_delete_is_gated_before_confirmation_and_releases_on_cancel_or_error():
    block = RECORDS.split("async function deleteRecord", 1)[1].split("onMounted", 1)[0]
    assert "const deletingRecord = ref(false)" in RECORDS
    assert "if (deletingRecord.value) return" in block
    assert "deletingRecord.value = true" in block
    assert "deletingRecord.value = false" in block
    assert "finally" in block
    assert "await requestConfirm(t('records.deleteConfirm'" in block
    assert ':disabled="deletingRecord"' in RECORDS


def test_historical_record_delete_has_the_same_duplicate_submit_gate():
    block = DAY.split("async function deleteRecord", 1)[1].split("// 切换日计划", 1)[0]
    assert "const deletingRecord = ref(false)" in DAY
    assert "if (deletingRecord.value) return" in block
    assert "deletingRecord.value = true" in block
    assert "deletingRecord.value = false" in block
    assert "finally" in block
    assert "await requestConfirm(t('dayDetail.deleteConfirm'" in block
    assert ':disabled="deletingRecord"' in DAY
