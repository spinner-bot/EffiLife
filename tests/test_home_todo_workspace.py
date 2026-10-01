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


def test_home_todo_completion_action_identifies_the_target_task():
    source = HOME.read_text(encoding="utf-8")
    assert "t('tasks.completeLabelFor', { title: todo.title })" in source
    assert I18N.read_text(encoding="utf-8").count("'tasks.completeLabelFor':") == 2


def test_home_summary_uses_the_shared_dynamic_priority_order():
    source = HOME.read_text(encoding="utf-8")
    assert "import { getPriorityScore } from '@/services/priority'" in source
    assert "TodoCategoryService.list()" in source
    assert "getPriorityScore(b, categoryById.get(b.category)).score" in source
    assert "b.updated_at.localeCompare(a.updated_at)" in source


def test_home_todo_summary_survives_category_storage_failure():
    source = HOME.read_text(encoding="utf-8")
    assert "TodoCategoryService.list().catch(() => [])" in source


def test_home_todos_stay_independent_from_event_plans():
    source = HOME.read_text(encoding="utf-8")
    assert "function openTodoPlan(todo: UnifiedTodo)" not in source
    assert "today-todo-plan" not in source


def test_home_keeps_event_plan_summary_copy_bilingual():
    source = I18N.read_text(encoding="utf-8")
    for key in ("home.openPlanCenter", "home.planModuleSummary"):
        assert source.count(f"'{key}'") == 2


def test_home_event_plan_summary_does_not_resolve_todo_plan_links():
    source = HOME.read_text(encoding="utf-8")
    assert "listPlanArchives" not in source
    assert "archivedPlanById" not in source
    assert "openTodoPlan" not in source


def test_home_refreshes_unified_summaries_after_workspace_changes():
    source = HOME.read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "scheduleWorkspaceSummaryRefresh" in source
    assert "appStore.refreshTodayData()" in source
    assert "refreshTodoSummary()" in source
    assert "refreshEventPlanSummary()" in source
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
    assert 'class="event-overview-header event-overview-header-action"' in source
