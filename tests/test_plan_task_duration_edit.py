from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_task_editor_exposes_non_negative_duration_input():
    source = PLANS.read_text(encoding="utf-8")
    assert "v-model.number=\"taskMinutes\"" in source
    assert 'type="number" min="0" step="1"' in source
    assert "t('plans.taskMinutes')" in source
    assert "addPlanTask(planId, taskSectionIndex.value, taskContent.value.trim(), minutes)" in source
    assert "updatePlanTask(planId, editedTaskId, nextContent, minutes)" in source
    assert "syncTodosFromPlanTask(planId, editedTaskId, nextContent, minutes)" in source
