from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_unified_archive_exports_all_workspace_datasets():
    source = ARCHIVE.read_text(encoding="utf-8")
    for dataset in ("app", "records", "todos", "todo_categories", "plan_helper"):
        assert f"'{dataset}'" in source
    assert "zip.file(`data/${name}.json`, datasetPayloads[name as keyof typeof datasetPayloads])" in source


def test_unified_archive_uses_canonical_json_before_hashing():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "function canonicalJson(value: unknown): string" in source
    assert ".sort()" in source
    assert "app: canonicalJson(app)" in source
    assert "records: canonicalJson(records)" in source
    assert "todos: canonicalJson(todos)" in source
    assert "todo_categories: canonicalJson(categories)" in source
    assert "plan_helper: canonicalJson(planHelper)" in source


def test_unified_archive_import_restores_todos_records_and_plan_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "await idbClear(STORE_NAMES.RECORDS)" in source
    assert "await idbClear(STORE_NAMES.TODOS)" in source
    assert "STORE_NAMES.PLAN_HELPER_SNAPSHOT" in source
    assert "requestPlanHelper('/api/data/import'" in source
    assert "data.planHelper.archives" in source
    assert "archives: Array.isArray(data.planHelper.archives)" in source


def test_unified_archive_carries_archived_plan_snapshots():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "await set(STORE_NAMES.PLAN_HELPER_SNAPSHOT, 'archives'" in source
    assert "data?: { plans?: unknown[]; archives?: unknown[] }" in source


def test_unified_archive_repairs_todo_record_links_in_both_directions():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "const recordTodoIds = new Map<string, string>()" in source
    assert "typeof candidate.todo_id === 'string'" in source
    assert "const reverseIds = [...recordTodoIds.entries()]" in source
    assert "const mergedIds = [...new Set([...validIds, ...reverseIds])]" in source
