from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_task_center_keeps_linked_todo_sync_failure_recoverable():
    source = TASKS.read_text(encoding="utf-8")
    assert "const todoPlanSyncRetryItem = ref<UnifiedTodo | null>(null)" in source
    assert "todoPlanSyncRetryItem.value = todo" in source
    assert "async function retryTodoPlanSync(): Promise<void>" in source
    assert "await TodoService.complete(todo.id)" in source
    assert "home.todoPlanSyncFailed" in source
    assert "@click=\"retryTodoPlanSync\"" in source


def test_task_center_does_not_retarget_ph_during_projection_retry():
    source = TASKS.read_text(encoding="utf-8")
    retry_block = source.split("async function retryTodoPlanSync", 1)[1].split("function startEdit", 1)[0]
    assert "completeTodoWithPlan" not in retry_block
    assert "completePlanTask" not in retry_block
