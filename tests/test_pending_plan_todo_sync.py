from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceSync.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
DB = ROOT / "time-helper" / "desk" / "src" / "storage" / "indexedDB.ts"


def test_pending_projection_queue_is_durable_and_startup_repair_is_non_blocking():
    source = SYNC.read_text(encoding="utf-8")
    app = APP.read_text(encoding="utf-8")
    db = DB.read_text(encoding="utf-8")
    assert "PENDING_PLAN_TODO_SYNC" in db
    assert "export async function queuePendingPlanTodoSync" in source
    assert "export async function repairPendingPlanTodoSync" in source
    assert "await completeLinkedPlanTodo(item.planId, item.planTaskId)" in source
    assert "void repairPendingPlanTodoSync().catch" in app


def test_pending_queue_storage_failures_are_best_effort():
    source = SYNC.read_text(encoding="utf-8")
    queue_block = source.split("export async function queuePendingPlanTodoSync", 1)[1].split("export async function clearPendingPlanTodoSync", 1)[0]
    clear_block = source.split("export async function clearPendingPlanTodoSync", 1)[1].split("/** Retry persisted", 1)[0]
    assert "console.warn('Failed to persist pending plan/todo sync:'" in queue_block
    assert "console.warn('Failed to clear pending plan/todo sync:'" in clear_block


def test_successful_projection_clears_stale_queue_entry():
    source = SYNC.read_text(encoding="utf-8")
    completion_block = source.split("export async function completeTodoWithPlan", 1)[1].split("/**", 1)[0]
    linked_block = source.split("export async function completeLinkedPlanTodo", 1)[1].split("/**", 1)[0]
    assert "await clearPendingPlanTodoSync(todo.related_plan_id, todo.related_plan_task_id)" in completion_block
    assert "await clearPendingPlanTodoSync(planId, planTaskId)" in linked_block
