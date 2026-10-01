from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk" / "src"


def test_plan_creation_collects_initial_content_then_opens_full_editor():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "const created = await createEventPlan(name, toDateTuple(planDate.value), sections)" in view
    assert "selectedPlan.value = await getPlanFull(createdId)" in view
    assert "view.value = 'detail'" in view
    assert "createEventPlanFromTemplate" in view
    assert "listPlanTemplates" in view
    assert "const createSections = ref<InitialPlanSection[]>([])" in view
    assert "v-for=\"(task, taskIndex) in section.tasks\"" in view
    assert "v-model=\"createTemplateId\"" not in view
    assert "plans.createTaskRequired" in view
    assert "plans.createAndEdit" in view
    assert "v-model=\"planName\"" in view
    assert "v-model=\"planDate\"" in view
    assert "sections: InitialPlanSection[] = []" in gateway
    assert "body: JSON.stringify({ name, date, sections })" in gateway


def test_plan_create_and_template_dates_default_to_the_local_current_day():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "const planDate = ref(toDateInput(new Date()))" in view
    assert "const templateDraftDate = ref(toDateInput(new Date()))" in view
    assert "planDate.value = toDateInput(new Date())" in view
    assert "function toDateInput(date: Date): string" in view
    assert "String(date.getMonth() + 1).padStart(2, '0')" in view
    assert "String(date.getDate()).padStart(2, '0')" in view


def test_plan_task_duration_is_explicitly_optional():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    i18n = (DESK / "i18n" / "index.ts").read_text(encoding="utf-8")

    assert "const taskMinutes = ref(0)" in view
    assert "plans.taskMinutesHint" in view
    assert "taskMinutes.value = task.time_minutes" in view
    assert "'plans.taskMinutesHint': '不确定时可以留为 0'" in i18n
    assert "'plans.taskMinutesHint': 'Leave it at 0 when you are not sure'" in i18n


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
    assert "createEventPlanFromTemplate(" in view


def test_template_entry_stays_outside_the_basic_create_modal():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    modal = view.split('<div v-if="showCreate"', 1)[1].split('</div>\n    </div>', 1)[0]

    assert "template-workspace" in view
    assert "openTemplatePicker" in view
    assert "v-model=\"planName\"" in modal
    assert "v-model=\"planDate\"" in modal
    assert "templateDraftId" not in modal
    assert "listPlanTemplates" not in modal


def test_plan_entries_are_not_converted_into_todos():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "TodoService" not in view
    assert "related_plan_id" not in view
    assert "related_plan_task_id" not in view


def test_plan_detail_has_its_own_progress_workflow():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "const linkedTodoIdsByTask" not in view
    assert "function isTaskLinkedToTodo" not in view
    assert "t('plans.viewTodo')" not in view
    assert "@submit.prevent=\"saveLog\"" in view
    assert "@click=\"startLog(task.internal_id)\"" in view
    assert "stopWorkspaceListener = onWorkspaceChanged(queueWorkspaceRefresh)" in view
    assert "stopWorkspaceListener()" in view


def test_plan_detail_does_not_bulk_create_todos():
    view = (DESK / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "async function addAllTasksToTodos()" not in view
    assert "linkPendingPlanTasksToTodos" not in view
    assert "t('plans.linkAllTodos'" not in view
