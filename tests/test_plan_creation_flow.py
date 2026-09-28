from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_plan_creation_collects_initial_sections_and_tasks_before_submission():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "const createSections = ref<InitialPlanSection[]>([])" in view
    assert "section.tasks" in view
    assert "createEventPlan(name, toDateTuple(planDate.value), sections)" in view
    assert "plans.createTaskRequired" in view
    assert "sections: InitialPlanSection[] = []" in gateway
    assert "body: JSON.stringify({ name, date, sections })" in gateway
    assert "export async function listPlanTemplates" in gateway
    assert "createEventPlanFromTemplate" in gateway
    assert "v-model=\"selectedTemplateId\"" in view
    assert "v-model=\"createTodos\"" in view
    assert "syncCreatedPlanTasks" in view


def test_mobile_plan_creation_preserves_section_and_task_shape():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "plan: [null, ...section.tasks" in gateway
    assert "t_m: Math.max(0, Number(task.time_minutes) || 0) / 6" in gateway
    assert "group: {}," in gateway


def test_template_creation_uses_the_existing_plan_helper_endpoint():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "request<{ templates?: PlanTemplateSummary[] }>('/api/templates')" in gateway
    assert "request<PlanFull>('/api/plans/from-template'" in gateway
    assert "template_id: templateId" in gateway


def test_created_todos_keep_both_plan_identifiers_for_bidirectional_sync():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "related_plan_id: String(plan.id)" in view
    assert "related_plan_task_id: String(task.internal_id)" in view
    assert "time_estimate: task.time_minutes" in view


def test_plan_detail_surfaces_existing_todo_links_without_duplicate_action():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "const linkedTodoTaskIds = ref(new Set<string>())" in view
    assert "function isTaskLinkedToTodo" in view
    assert "isTaskLinkedToTodo(task) ? t('plans.todoLinked') : t('plans.linkTodo')" in view
    assert "isLoading || isTaskLinkedToTodo(task)" in view
    assert "onWorkspaceChanged((source)" in view
    assert "stopWorkspaceListener()" in view
    assert "!['archived', 'cancelled'].includes(todo.status)" in view


def test_plan_detail_can_bulk_link_unfinished_tasks_without_duplicates():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "async function addAllTasksToTodos()" in view
    assert "const pendingTasks = plan.sections" in view
    assert "!task.finish" in view
    assert "t('plans.todosBulkCreated'" in view
    assert "t('plans.todosAllLinked'" in view
