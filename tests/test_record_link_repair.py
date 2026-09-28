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


def test_startup_repairs_only_provably_stale_plan_task_links():
    source = SYNC.read_text(encoding="utf-8")
    assert "async function repairTodoPlanTaskLinks()" in source
    assert "from './planGateway'" in source
    assert "listPlanSummaries" in source
    assert "getPlanTasks" in source
    assert "taskIds.has(String(todo.related_plan_task_id))" in source
    assert "related_plan_id: undefined" in source


def test_app_runs_plan_task_link_repair_after_record_link_repair():
    source = APP.read_text(encoding="utf-8")
    assert "repairTodoPlanTaskLinks" in source
    assert "void repairTodoPlanTaskLinks()" in source
    assert source.index("runtimeReady.value = true") < source.index("void repairTodoPlanTaskLinks()")
