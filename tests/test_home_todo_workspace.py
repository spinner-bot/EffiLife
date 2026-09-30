from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_home_reads_and_sorts_active_todos_for_summary():
    source = HOME.read_text(encoding="utf-8")
    assert "const todayTodos = ref<UnifiedTodo[]>([])" in source
    assert "TodoService.list()" in source
    assert "todayTodos.value = [...active]" in source
    assert ".slice(0, 3)" in source
    assert "router.push('/tasks')" in source


def test_home_todo_workspace_has_bilingual_copy():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "home.todayTodosEyebrow",
        "home.todayTodos",
        "home.viewTodos",
        "home.noTodos",
        "home.createTodoHint",
        "home.openTodoCenter",
        "home.noDeadline",
        "home.moreTodos",
    ):
        assert source.count(f"'{key}'") == 2


def test_home_todos_support_quick_completion_without_leaving_home():
    source = HOME.read_text(encoding="utf-8")
    assert "async function completeHomeTodo(todo: UnifiedTodo)" in source
    assert "await TodoService.complete(todo.id)" in source
    assert "class=\"today-todo-complete\"" in source
    assert "await refreshTodoSummary()" in source


def test_home_summary_uses_the_shared_dynamic_priority_order():
    source = HOME.read_text(encoding="utf-8")
    assert "import { getPriorityScore } from '@/services/priority'" in source
    assert "TodoCategoryService.list()" in source
    assert "getPriorityScore(b, categoryById.get(b.category)).score" in source
    assert "b.updated_at.localeCompare(a.updated_at)" in source


def test_home_todo_summary_survives_category_storage_failure():
    source = HOME.read_text(encoding="utf-8")
    assert "TodoCategoryService.list().catch(() => [])" in source


def test_home_linked_todos_can_return_to_their_plan_task():
    source = HOME.read_text(encoding="utf-8")
    assert "function openTodoPlan(todo: UnifiedTodo)" in source
    assert "plan: todo.related_plan_id" in source
    assert "task: todo.related_plan_task_id" in source
    assert 'class="today-todo-plan"' in source
    assert "home.openPlanReference" in source


def test_home_plan_reference_copy_is_bilingual():
    source = I18N.read_text(encoding="utf-8")
    for key in ("home.openPlanReference", "home.linkedPlan"):
        assert source.count(f"'{key}'") == 2


def test_home_resolves_archived_plan_references_without_hiding_them():
    source = HOME.read_text(encoding="utf-8")
    assert "listPlanArchives" in source
    assert "archivedPlanById" in source
    assert "home.archivedPlan" in source


def test_home_refreshes_unified_summaries_after_workspace_changes():
    source = HOME.read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "scheduleWorkspaceSummaryRefresh" in source
    assert "Promise.all([refreshTodoSummary(), refreshEventPlanSummary()])" in source
    assert "workspaceRefreshTimer" in source
    assert "stopWorkspaceListener()" in source


def test_home_dashboard_previews_multiple_active_plans_without_merging_todos():
    source = HOME.read_text(encoding="utf-8")
    assert "const eventPlanPreview = computed(() => eventPlans.value.slice(0, 3))" in source
    assert "plan.completed_tasks" in source
    assert "plan.progress_percentage" in source
    assert "home.moreActivePlans" in source
    assert "event-plan-preview" in source


def test_home_dashboard_can_deep_link_to_an_individual_plan():
    source = HOME.read_text(encoding="utf-8")
    assert "function openEventPlan(plan: PlanSummary)" in source
    assert "query: { plan: plan.id }" in source
    assert 'class="event-plan-preview-row"' in source
    assert '@click.stop="openEventPlan(plan)"' in source
    assert 'role="link" tabindex="0"' in source
