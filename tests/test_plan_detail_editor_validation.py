from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_editors_expose_native_required_constraints():
    assert '<input v-model="planName" required />' in VIEW
    assert '<input v-model="planDate" type="date" required />' in VIEW
    assert ':placeholder="t(\'plans.sectionName\')" required />' in VIEW
    assert '<input v-model="taskContent" required autofocus />' in VIEW
    assert '<input v-model="groupTitle" required autofocus />' in VIEW


def test_plan_action_buttons_have_explicit_non_submit_types():
    clickable_buttons = [line for line in VIEW.splitlines() if '<button' in line and '@click' in line]
    assert clickable_buttons
    assert all('type="button"' in line for line in clickable_buttons)


def test_plan_creation_starts_with_local_today_and_a_real_editable_task():
    assert "planDate.value = toDateInput(new Date())" in VIEW
    assert "createSections.value = [{ name: '', info: '', tasks: [{ content: '', time_minutes: 0 }] }]" in VIEW
    assert "const created = await createEventPlan(name, toDateTuple(planDate.value), sections)" in VIEW
    assert "selectedPlan.value = await getPlanFull(createdId)" in VIEW
    assert "view.value = 'detail'" in VIEW


def test_plan_creation_modal_exposes_sections_and_tasks_before_submit():
    assert 'class="create-sections"' in VIEW
    assert 'v-for="(section, sectionIndex) in createSections"' in VIEW
    assert 'v-for="(task, taskIndex) in section.tasks"' in VIEW
    assert '@click="addCreateSection"' in VIEW
    assert '@click="addCreateTask(section)"' in VIEW
