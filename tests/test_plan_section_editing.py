from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts"
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_gateway_exposes_section_edit_and_soft_delete_operations():
    source = GATEWAY.read_text(encoding="utf-8")
    assert "export async function updatePlanSection" in source
    assert "method: 'PUT'" in source
    assert "export async function deletePlanSection" in source
    assert "section.plan = [null]" in source
    assert "without shifting" in source


def test_plan_center_exposes_section_edit_and_cleans_task_links():
    source = PLANS.read_text(encoding="utf-8")
    assert "startSectionEdit(section)" in source
    assert "deleteSection(section)" in source
    assert "unlinkTodosFromPlanTask(planId, task.internal_id)" in source
    assert "unlinkTodosFromPlanTask(planId, task.display_id)" in source


def test_single_task_delete_cleans_internal_and_display_links():
    source = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "async function deleteTask(taskId: string, displayTaskId = taskId)" in source
    assert "await unlinkTodosFromPlanTask(planId, displayTaskId)" in source
    assert "@click=\"deleteTask(task.internal_id, task.display_id)\"" in source
    assert "editingSectionIndex" in source


def test_section_edit_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "plans.editSection",
        "plans.saveSection",
        "plans.deleteSection",
        "plans.deleteSectionConfirm",
        "plans.sectionUnavailable",
    ):
        assert source.count(f"'{key}'") == 2
