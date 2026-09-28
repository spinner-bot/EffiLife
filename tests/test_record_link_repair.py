from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"


def test_startup_repairs_only_unresolvable_record_links():
    source = SYNC.read_text(encoding="utf-8")
    assert "async function repairTodoTimeRecordLinks()" in source
    assert "recordIds.has(id)" in source
    assert "return 0" in source


def test_app_runs_link_repair_after_storage_migration():
    source = APP.read_text(encoding="utf-8")
    assert "repairTodoTimeRecordLinks" in source
    assert "await TodoService.migrateLegacyLocalStorage()" in source
    assert "await repairTodoTimeRecordLinks()" in source
