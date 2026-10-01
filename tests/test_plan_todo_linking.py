from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_detail_does_not_create_or_duplicate_todos():
    source = PLANS.read_text(encoding="utf-8")
    assert "TodoService" not in source
    assert "TodoService.create" not in source
    assert "related_plan_id" not in source
    assert "related_plan_task_id" not in source
    assert "addTaskToTodos" not in source


def test_plan_todo_linking_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    import re
    zh_match = re.search(r"'zh-CN':\s*\{(?P<body>.*?)\n  \},\n  'en-US':", source, re.S)
    en_match = re.search(r"'en-US':\s*\{(?P<body>.*?)\n  \},\n}\n\nfunction readLocale", source, re.S)
    assert zh_match and en_match
    for key in ("plans.linkTodo", "plans.viewTodo", "plans.todoCreated", "plans.todoAlreadyLinked", "plans.todoCreateFailed"):
        assert zh_match.group('body').count(f"'{key}'") == 1
        assert en_match.group('body').count(f"'{key}'") == 1


def test_task_center_can_open_the_linked_plan_task():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "function openTodoPlan(todo: UnifiedTodo)" in tasks
    assert "path: '/plans'" in tasks
    assert "task: todo.related_plan_task_id" in tasks
    assert "@click=\"openTodoPlan(todo)\"" in tasks
    assert "#{{ todo.related_plan_task_id }}" in tasks
    assert "planTaskById[todo.related_plan_task_id]" not in tasks
    assert "...(archivedPlan ? { archive: archivedPlan.file } : { plan: todo.related_plan_id })" in tasks


def test_editing_a_linked_todo_updates_the_source_plan_task_first():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "updatePlanTask" in tasks
    assert "const linkedTaskChanged = Boolean" in tasks
    assert "await updatePlanTask(todo.related_plan_id as string, todo.related_plan_task_id as string" in tasks
    assert "errorMessage.value = t('tasks.planSyncFailed')" in tasks


def test_plan_mutations_expose_success_feedback_in_both_locales():
    plans = PLANS.read_text(encoding="utf-8")
    source = I18N.read_text(encoding="utf-8")
    assert "function showPlanSaved(): void" in plans
    assert "notifyToast(t('plans.saved'), 'success')" in plans
    assert source.count("'plans.saved':") == 2
