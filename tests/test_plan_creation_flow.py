from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_plan_creation_collects_a_first_section_and_task_before_opening_editor():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "const created = await createEventPlan(name, toDateTuple(planDate.value), [{" in view
    assert "name: section," in view
    assert "tasks: [{ content: task, time_minutes: Math.max(0, Number(createTaskMinutes.value) || 0) }]," in view
    assert "createEventPlanFromTemplate" in view
    assert "listPlanTemplates" in view
    assert "const createSectionName = ref('')" in view
    assert "const createTaskContent = ref('')" in view
    assert "const createTaskMinutes = ref(30)" in view
    assert "const createTodos = ref(false)" in view
    assert "plans.firstActionTitle" in view
    assert "plans.firstActionHint" in view
    assert "plans.createTaskRequired" in view
    assert "v-model=\"createTemplateId\"" in view
    assert "plans.templateManual" in view
    assert "plans.templateSelected" in view
    assert "v-model=\"createTodos\"" in view
    assert "linkPendingPlanTasksToTodos(selectedPlan.value)" in view
    assert "catch {\n        notifyToast(t('plans.todoSyncFailed'), 'error')\n      }" in view
    assert "plans.createAndEdit" in view
    assert "v-model=\"planName\"" in view
    assert "v-model=\"planDate\"" in view
    assert "sections: InitialPlanSection[] = []" in gateway
    assert "body: JSON.stringify({ name, date, sections })" in gateway


def test_mobile_plan_creation_preserves_section_and_task_shape():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "plan: [null, ...section.tasks" in gateway
    assert "t_m: Math.max(0, Number(task.time_minutes) || 0) / 6" in gateway
    assert "group: {}," in gateway
    assert "planDataSource.value = 'mobile'" in gateway
    assert "planDataSource.value = 'service'" in gateway
    assert "if ((options.method || 'GET').toUpperCase() !== 'GET') {" in gateway
    assert "notifyWorkspaceChanged('plans')" in gateway


def test_mobile_plan_templates_are_local_and_keep_group_semantics():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "const MOBILE_TEMPLATE_DEFINITIONS" in gateway
    assert "return MOBILE_TEMPLATE_DEFINITIONS.map(mobileTemplateSummary)" in gateway
    assert "const template = MOBILE_TEMPLATE_DEFINITIONS.find((candidate) => candidate.id === templateId)" in gateway
    assert "await addPlanGroup(" in gateway
    assert "group.start" in gateway and "group.end" in gateway
    assert "plans.templateMissing" in gateway


def test_template_creation_uses_the_existing_plan_helper_endpoint():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "request<{ templates?: PlanTemplateSummary[] }>('/api/templates')" in gateway
    assert "planDataSource.value = 'service'" in gateway
    assert "request<PlanFull>('/api/plans/from-template'" in gateway
    assert "template_id: templateId" in gateway
    assert "locale = 'zh-CN'" in gateway
    assert "locale })" in gateway
    assert "createEventPlanFromTemplate(createTemplateId.value, name, toDateTuple(planDate.value), locale.value)" in view


def test_detail_editor_created_todos_keep_both_plan_identifiers_for_bidirectional_sync():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "related_plan_id: String(plan.id)" in view
    assert "related_plan_task_id: String(task.internal_id)" in view
    assert "time_estimate: task.time_minutes" in view


def test_plan_detail_surfaces_existing_todo_links_without_duplicate_action():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "const linkedTodoIdsByTask = ref(new Map<string, string>())" in view
    assert "function isTaskLinkedToTodo" in view
    assert "isTaskLinkedToTodo(task) ? t('plans.viewTodo') : t('plans.linkTodo')" in view
    assert ':disabled="isLoading"' in view
    assert "t('plans.viewTodo')" in view
    assert "router.push({ path: '/tasks', query: { todo: todoId } })" in view
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
