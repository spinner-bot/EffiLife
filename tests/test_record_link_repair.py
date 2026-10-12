from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"


def test_startup_repairs_only_unresolvable_record_links():
    source = SYNC.read_text(encoding="utf-8")
    assert "async function repairTodoTimeRecordLinks()" in source
    assert "recordIds.has(id)" in source
    assert "return 0" in source
    repair = source.split("async function repairTodoTimeRecordLinks", 1)[1].split("/** Remove plan-task", 1)[0]
    assert "const changedRecords: Array<{ key: string; previous: TimeRecord[]; next: TimeRecord[] }> = []" in repair
    assert "await idbSet(STORE_NAMES.RECORDS, entry.key, entry.previous)" in repair
    assert "Failed to roll back todo/time-record link repair" in repair


def test_app_runs_link_repair_after_storage_migration():
    source = APP.read_text(encoding="utf-8")
    assert "repairTodoTimeRecordLinks" in source
    assert "await TodoService.migrateLegacyLocalStorage()" in source
    assert "await repairTodoTimeRecordLinks()" in source
    assert "Link repair is recoverable maintenance" in source
    assert "console.warn('Failed to repair todo/time-record links during startup:'" in source


def test_startup_repairs_only_provably_stale_plan_task_links():
    source = SYNC.read_text(encoding="utf-8")
    assert "async function repairTodoPlanTaskLinks()" in source
    assert "from './planGateway'" in source
    assert "listPlanSummaries" in source
    assert "getPlanTasks" in source
    assert "planDataSource" in source
    assert "if (String(planDataSource.value) === 'cache') return 0" in source
    assert "A task request may fall back to the local snapshot" in source
    assert "An absent active summary is not proof that the plan was deleted" in source
    assert "taskIdsByPlan.set(planId, new Set())" not in source
    assert "taskIds.has(String(todo.related_plan_task_id))" in source
    assert "related_plan_id: undefined" in source


def test_plan_link_repair_does_not_treat_reused_display_ids_as_stable_links():
    source = SYNC.read_text(encoding="utf-8")
    repair_block = source.split("async function repairTodoPlanTaskLinks()", 1)[1]
    repair_block = repair_block.split("export", 1)[0]
    assert "new Set(tasks.map((task) => String(task.internal_id)))" in repair_block
    assert "flatMap((task) => [String(task.internal_id), String(task.display_id)])" not in repair_block


def test_startup_preserves_links_to_archived_plans():
    source = SYNC.read_text(encoding="utf-8")
    absent_plan_branch = source.split("for (const planId of new Set(linkedTodos.map", 1)[1]
    absent_plan_branch = absent_plan_branch.split("try {", 1)[0]
    assert "if (!planIds.has(planId))" in absent_plan_branch
    assert "archived plans" in absent_plan_branch
    assert "continue" in absent_plan_branch


def test_app_runs_plan_task_link_repair_after_record_link_repair():
    source = APP.read_text(encoding="utf-8")
    assert "repairTodoPlanTaskLinks" in source
    assert "void repairTodoPlanTaskLinks()" in source
    assert source.index("runtimeReady.value = true") < source.index("void repairTodoPlanTaskLinks()")


def test_plan_task_link_repair_has_a_recoverable_startup_error_boundary():
    source = APP.read_text(encoding="utf-8")
    repair_call = source.split("void repairTodoPlanTaskLinks()", 1)[1].split("// 启动背景音乐", 1)[0]
    assert ".catch((error) =>" in repair_call
    assert "Failed to repair todo/plan links after startup:" in repair_call


def test_startup_repair_cleans_time_records_pointing_to_deleted_todos():
    sync = SYNC.read_text(encoding="utf-8")
    assert "const todoIds = new Set(todos.map((todo) => todo.id))" in sync
    assert "if (!record?.todo_id || todoIds.has(record.todo_id)) return record" in sync
    assert "delete nextRecord.todo_id" in sync
    assert "changedRecords.push" in sync
    assert "await idbSet(STORE_NAMES.RECORDS, entry.key, entry.next)" in sync


def test_startup_plan_link_repair_rolls_back_partial_multi_todo_repairs():
    sync = SYNC.read_text(encoding="utf-8")
    repair = sync.split("export async function repairTodoPlanTaskLinks", 1)[1]
    assert "const repairedTodos: typeof linkedTodos = []" in repair
    assert "await TodoService.update(todo.id, {" in repair
    assert "todo.related_plan_id" in repair
    assert "todo.related_plan_task_id" in repair
    assert "Failed to roll back plan-task link repair" in repair
