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


def test_archive_stats_use_unified_plan_gateway_fallback_and_expose_source():
    source = ARCHIVE.read_text(encoding="utf-8")
    stats = source.split("export async function getDataStats", 1)[1]

    assert "const eventPlanData = await collectPlanHelperDataWithCache()" in stats
    assert "eventPlanCount: eventPlanData.plans.length" in stats
    assert "archivedEventPlanCount: eventPlanData.archives?.length || 0" in stats
    assert "eventPlanSource: !eventPlanData.available" in stats
    assert "'live' | 'cache' | 'snapshot' | 'unavailable'" in stats


def test_archive_records_do_not_merge_stale_legacy_dates_into_indexeddb():
    source = ARCHIVE.read_text(encoding="utf-8")
    records = source.split("async function getAllRecords", 1)[1]

    assert "const indexedDBRecords: Record<string, unknown[]> = {}" in records
    assert "if (Object.keys(indexedDBRecords).length > 0) return indexedDBRecords" in records


def test_archive_import_validates_record_buckets_before_writing():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "function normalizeImportedRecords(raw: unknown)" in source
    assert "const records = normalizeImportedRecords(datasets.records)" in source
    assert "const legacyRecords = legacy.records === undefined ? undefined : normalizeImportedRecords(legacy.records)" in source
    assert "settings.archive.recordsInvalid" in source
    assert "settings.archive.recordsDateInvalid" in source


def test_archive_import_repairs_todo_record_links_against_imported_records():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "function repairImportedTodoRecordLinks" in source
    assert "const repairedRecordLinks = repairImportedTodoRecordLinks" in source
    assert "recordIds.has(id)" in source


def test_archive_import_reports_repaired_todo_record_links():
    source = ARCHIVE.read_text(encoding="utf-8")
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert "importRepairs: { todoRecordLinks: repairedRecordLinks.repaired" in source
    assert "settings.archive.repairedTodoRecordLinks" in source
    assert i18n.count("settings.archive.repairedTodoRecordLinks") == 2


def test_archive_import_repairs_plan_task_links_only_with_available_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    i18n = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert "function repairImportedTodoPlanLinks" in source
    assert "snapshot.available !== true" in source
    assert "taskIdsByPlan.get(String(todo.related_plan_id))" in source
    assert "settings.archive.repairedTodoPlanTaskLinks" in source
    assert i18n.count("settings.archive.repairedTodoPlanTaskLinks") == 2


def test_archive_import_repairs_plan_task_links_against_archived_snapshots():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "archives?: unknown" in source
    assert "snapshot.archives" in source
    assert "payload?.plan" in source
    assert "const rawPlans = [" in source


def test_archive_import_unions_task_ids_when_active_and_archived_plan_ids_repeat():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "const knownTaskIds = taskIdsByPlan.get(planId)" in source
    assert "new Set([...knownTaskIds, ...taskIds])" in source


def test_archive_import_does_not_write_mobile_plan_snapshot_twice():
    source = ARCHIVE.read_text(encoding="utf-8")
    restore = source.split("const warnings: string[] = []", 1)[1].split("notifyWorkspaceChanged('archive')", 1)[0]
    assert restore.count("await idbSet(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'plans', data.planHelper.plans)") == 1


def test_archive_import_replaces_nullable_optional_datasets_without_breaking_legacy_missing_fields():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "async function restoreOptionalJsonDataset(" in source
    assert "if (value === undefined) return" in source
    assert "if (value === null)" in source
    assert "localStorage.removeItem(localKey)" in source
    assert "await idbClear(storeName)" in source
    assert "restoreOptionalJsonDataset(STORAGE_KEYS.CONFIG" in source
    assert "restoreOptionalJsonDataset(STORAGE_KEYS.CHECKIN" in source
