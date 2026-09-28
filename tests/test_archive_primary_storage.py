import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_collects_core_data_from_indexeddb_before_legacy_mirror():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "async function readCoreJSON" in source
    assert "await get<T>(storeName, storeKey)" in source
    collect = source.split("async function collectAllData", 1)[1].split("export async function exportArchive", 1)[0]
    for key in ("config", "plans", "scheduleRules", "manualPlans", "audioSettings", "eventSettings", "eventInbox", "warningInbox", "dailyTrigger", "checkin"):
        assert re.search(rf"{key}: await readCoreJSON", collect)


def test_archive_stats_read_primary_values_from_indexeddb():
    source = ARCHIVE.read_text(encoding="utf-8")
    stats = source.split("export async function getDataStats", 1)[1]

    for store_key in ("CONFIG", "PLANS", "AUDIO_SETTINGS", "EVENT_SETTINGS", "CHECKIN"):
        assert f"readCoreJSON" in stats
        assert f"STORE_NAMES.{store_key}" in stats


def test_archive_records_do_not_merge_stale_legacy_dates_into_indexeddb():
    source = ARCHIVE.read_text(encoding="utf-8")
    records = source.split("async function getAllRecords", 1)[1]

    assert "const indexedDBRecords: Record<string, unknown[]> = {}" in records
    assert "if (Object.keys(indexedDBRecords).length > 0) return indexedDBRecords" in records


def test_archive_import_validates_record_buckets_before_writing():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "function normalizeImportedRecords(raw: unknown)" in source
    assert "const records = normalizeImportedRecords(datasets.records)" in source
    assert "const records = normalizeImportedRecords(legacy.records)" in source
    assert "必须是数组" in source


def test_archive_import_repairs_todo_record_links_against_imported_records():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "function repairImportedTodoRecordLinks" in source
    assert "const repairedTodos = repairImportedTodoRecordLinks" in source
    assert "recordIds.has(id)" in source


def test_archive_import_reports_repaired_todo_record_links():
    source = ARCHIVE.read_text(encoding="utf-8")
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert "importRepairs: { todoRecordLinks: repairedTodos.repaired }" in source
    assert "settings.archive.repairedTodoRecordLinks" in source
    assert i18n.count("settings.archive.repairedTodoRecordLinks") == 2
