import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_collects_core_data_from_indexeddb_before_legacy_mirror():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "async function readCoreJSON" in source
    assert "await get<T>(storeName, storeKey)" in source
    collect = source.split("async function collectAllData", 1)[1].split("export async function exportArchive", 1)[0]
    for key in ("config", "plans", "scheduleRules", "manualPlans"):
        assert re.search(rf"{key}: await readCoreJSON", collect)


def test_archive_stats_read_primary_values_from_indexeddb():
    source = ARCHIVE.read_text(encoding="utf-8")
    stats = source.split("export async function getDataStats", 1)[1]

    for store_key in ("CONFIG", "PLANS"):
        assert f"readCoreJSON" in stats
        assert f"STORE_NAMES.{store_key}" in stats
    assert "hasAudioSettings: !!readJSON(STORAGE_KEYS.AUDIO_SETTINGS)" in stats
    assert "hasEventSettings: !!readJSON(STORAGE_KEYS.EVENT_SETTINGS)" in stats
    assert "hasCheckin: !!readJSON(STORAGE_KEYS.CHECKIN)" in stats


def test_archive_records_do_not_merge_stale_legacy_dates_into_indexeddb():
    source = ARCHIVE.read_text(encoding="utf-8")
    records = source.split("async function getAllRecords", 1)[1]

    assert "const indexedDBRecords: Record<string, unknown[]> = {}" in records
    assert "if (Object.keys(indexedDBRecords).length > 0) return indexedDBRecords" in records
