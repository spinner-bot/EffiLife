from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_detail_links_todos_without_merging_module_entities():
    source = PLANS.read_text(encoding="utf-8")
    assert "TodoService.create" in source
    assert "related_plan_id" in source
    assert "related_plan_task_id" in source
    assert "function createLinkedTodos" in source
    assert "const linkedTodoCount = computed" in source
    assert "t('plans.linkedTodos')" in source
    assert 'class="task-todo-link"' in source
    assert 'linkedTodoTaskIds.has(task.internal_id)' in source
    assert "function completeTask" in source
    assert "completeLinkedTodos" in source
    # PH remains the owner of plan-task mutations; TD receives only a relation.
    assert "updatePlanTask" not in (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_todo_linking_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    import re
    zh_match = re.search(r"'zh-CN':\s*\{(?P<body>.*?)\n  \},\n  'en-US':", source, re.S)
    en_match = re.search(r"'en-US':\s*\{(?P<body>.*?)\n  \},\n}\n\nfunction readLocale", source, re.S)
    assert zh_match and en_match
    for key in ("plans.linkAllTodos", "plans.linkedTodos", "plans.todosAllLinked", "plans.todosBulkCreated", "plans.todoCreateFailed"):
        assert zh_match.group('body').count(f"'{key}'") == 1
        assert en_match.group('body').count(f"'{key}'") == 1


def test_task_center_does_not_open_plan_tasks_from_todos():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "function openTodoPlan" not in tasks
    assert "todo.related_plan_task_id" not in tasks


def test_editing_a_todo_does_not_update_a_plan_task():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "updatePlanTask" not in tasks
    assert "linkedTaskChanged" not in tasks
    assert "tasks.planSyncFailed" not in tasks


def test_plan_mutations_expose_success_feedback_in_both_locales():
    plans = PLANS.read_text(encoding="utf-8")
    source = I18N.read_text(encoding="utf-8")
    assert "function showPlanSaved(): void" in plans
    assert "notifyToast(t('plans.saved'), 'success')" in plans
    assert source.count("'plans.saved':") == 2
