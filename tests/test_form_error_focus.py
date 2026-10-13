from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_td_creation_failure_preserves_and_refocuses_title_input():
    create = TASKS.split("async function addTodo()", 1)[1].split("async function loadCategories", 1)[0]
    assert "errorMessage.value = getUserFacingError(error, t('tasks.error.create'))" in create
    assert "await nextTick()" in create
    assert "newTaskInput.value?.focus()" in create


def test_ph_creation_failure_preserves_and_refocuses_plan_name_input():
    create = PLANS.split("async function createPlan()", 1)[1].split("async function savePlanMeta", 1)[0]
    assert "errorMessage.value = getUserFacingError(error, t('plans.unavailable'))" in create
    assert "await nextTick()" in create
    assert "createNameInput.value?.focus()" in create
