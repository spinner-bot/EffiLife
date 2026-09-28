from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_unified_archive_exports_all_workspace_datasets():
    source = ARCHIVE.read_text(encoding="utf-8")
    for dataset in ("app", "records", "todos", "todo_categories", "plan_helper"):
        assert f"'{dataset}'" in source
    assert "zip.file(`data/${name}.json`, datasetPayloads[name as keyof typeof datasetPayloads])" in source


def test_unified_archive_import_restores_todos_records_and_plan_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "await idbClear(STORE_NAMES.RECORDS)" in source
    assert "await idbClear(STORE_NAMES.TODOS)" in source
    assert "STORE_NAMES.PLAN_HELPER_SNAPSHOT" in source
    assert "requestPlanHelper('/api/data/import'" in source
