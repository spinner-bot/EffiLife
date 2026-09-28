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


def test_mobile_plan_creation_preserves_section_and_task_shape():
    gateway = (DESK / "services" / "planGateway.ts").read_text(encoding="utf-8")

    assert "plan: [null, ...section.tasks" in gateway
    assert "t_m: Math.max(0, Number(task.time_minutes) || 0) / 6" in gateway
    assert "group: {}," in gateway
