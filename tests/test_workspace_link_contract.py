from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_todo_deletion_cleans_time_record_references_without_deleting_history():
    todos = (DESK / "services" / "todoService.ts").read_text(encoding="utf-8")
    sync = (DESK / "services" / "workspaceSync.ts").read_text(encoding="utf-8")
    assert "DataService.unlinkTodoFromRecords(id)" in todos
    assert "Remove a deleted time-record ID" in sync
    assert "time_spent" not in sync.split("export async function unlinkTodoFromTimeRecord", 1)[1].split("export async function repairTodoTimeRecordLinks", 1)[0]


def test_plan_task_removal_cleans_only_the_cross_module_reference():
    sync = (DESK / "services" / "workspaceSync.ts").read_text(encoding="utf-8")
    plans = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "export async function unlinkTodosFromPlanTask" in sync
    assert "related_plan_id: undefined" in sync
    assert "related_plan_task_id: undefined" in sync
    assert "unlinkTodosFromPlanTask(planId, taskId)" in plans


def test_startup_and_archive_import_repair_stale_links_conservatively():
    app = (DESK / "App.vue").read_text(encoding="utf-8")
    archive = (DESK / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    sync = (DESK / "services" / "workspaceSync.ts").read_text(encoding="utf-8")
    assert "repairTodoTimeRecordLinks()" in app
    assert "repairTodoPlanTaskLinks()" in app
    assert "repairImportedTodoRecordLinks" in archive
    assert "repairImportedTodoPlanLinks" in archive
    assert "planDataSource.value === 'cache'" in sync
