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


def test_plan_center_cleans_links_when_a_section_is_soft_deleted():
    source = PLANS.read_text(encoding="utf-8")
    assert "startSectionEdit(section)" in source
    assert "deleteSection(section)" in source
    assert "unlinkTodosFromPlanTask(planId, taskId)" in source


def test_single_task_delete_also_clears_its_stale_todo_relation():
    source = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "async function deleteTask(taskId: string)" in source
    assert "unlinkTodosFromPlanTask(planId, taskId)" in source
    assert "@click=\"deleteTask(task.internal_id)\"" in source
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
