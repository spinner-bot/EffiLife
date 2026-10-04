from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAY_DETAIL = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_historical_day_detail_refreshes_after_network_recovery():
    assert "if (source === 'records' || source === 'plans' || source === 'archive' || source === 'network') void retryLoadData()" in DAY_DETAIL
    assert "async function retryLoadData(): Promise<void>" in DAY_DETAIL


def test_historical_day_detail_localizes_display_date_without_changing_route_storage():
    assert "const displayDate = computed(() =>" in DAY_DETAIL
    assert "parseLocalDate(dateStr.value)" in DAY_DETAIL
    assert "month: '2-digit'" in DAY_DETAIL
    assert "day: '2-digit'" in DAY_DETAIL
    assert "<h1>{{ displayDate }} {{ t('dayDetail.titleSuffix') }}</h1>" in DAY_DETAIL


def test_historical_day_detail_delete_resolves_current_record_by_stable_id():
    assert "const requestedRecord = records.value[index]" in DAY_DETAIL
    assert "const resolvedIndex = requestedRecord?.id" in DAY_DETAIL
    assert "await DataService.deleteRecord(resolvedIndex, dateStr.value)" in DAY_DETAIL
    assert "dayDetail.recordMissing" in DAY_DETAIL
