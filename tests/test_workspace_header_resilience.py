from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_header_can_wrap_without_collapsing_title_or_actions():
    assert ".plans-header { display: flex; flex-wrap: wrap;" in PLANS
    assert ".plans-title-block { flex: 1 1 220px; min-width: 0; }" in PLANS
    assert ".plan-entry-actions { display: flex; flex-wrap: wrap;" in PLANS


def test_task_header_can_wrap_without_collapsing_title_or_counts():
    assert ".task-header { display: flex; flex-wrap: wrap;" in TASKS
    assert ".task-title-block { flex: 1 1 220px; min-width: 0; }" in TASKS
    assert ".task-counts { display: flex; flex-wrap: wrap;" in TASKS
