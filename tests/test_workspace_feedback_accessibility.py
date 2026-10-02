from pathlib import Path


VIEWS = Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views"
PLANS = (VIEWS / "PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (VIEWS / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_workspace_announces_errors_and_successful_saves():
    assert '<p v-if="errorMessage" class="plans-error" role="alert">' in PLANS
    assert '<div v-if="errorMessage" class="plans-error" role="alert">' in PLANS
    assert '<div v-if="successMessage" class="plans-success" role="status" aria-live="polite">' in PLANS


def test_todo_workspace_announces_errors_to_assistive_technology():
    assert '<span v-if="errorMessage" class="task-error" role="alert">' in TASKS
