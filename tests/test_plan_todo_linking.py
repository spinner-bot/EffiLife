from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_detail_can_create_a_linked_unified_todo_without_duplicates():
    source = PLANS.read_text(encoding="utf-8")
    assert "import { TodoService }" in source
    assert "TodoService.list()" in source
    assert "TodoService.create({" in source
    assert "related_plan_id: planId" in source
    assert "related_plan_task_id: String(task.internal_id)" in source
    assert "todoAlreadyLinked" in source
    assert "@click=\"addTaskToTodos(task)\"" in source


def test_plan_todo_linking_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("plans.linkTodo", "plans.todoCreated", "plans.todoAlreadyLinked", "plans.todoCreateFailed"):
        assert source.count(f"'{key}'") == 2


def test_task_center_can_open_the_linked_plan_task():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "function openTodoPlan(todo: UnifiedTodo)" in tasks
    assert "path: '/plans'" in tasks
    assert "task: todo.related_plan_task_id" in tasks
    assert "@click=\"openTodoPlan(todo)\"" in tasks


def test_editing_a_linked_todo_updates_the_source_plan_task_first():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "updatePlanTask" in tasks
    assert "const linkedTaskChanged = Boolean" in tasks
    assert "await updatePlanTask(todo.related_plan_id as string, todo.related_plan_task_id as string" in tasks
    assert "errorMessage.value = t('tasks.planSyncFailed')" in tasks
