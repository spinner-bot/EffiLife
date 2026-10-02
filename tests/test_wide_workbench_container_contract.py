from pathlib import Path


SRC = Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views"
PLANS = (SRC / "PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (SRC / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_center_expands_its_desktop_working_area():
    assert "@media (min-width: 1100px)" in PLANS
    assert ".plans-header, .plans-content { max-width: min(1440px, calc(100vw - 64px)); }" in PLANS


def test_task_center_expands_its_desktop_working_area():
    assert "@media (min-width: 1100px)" in TASKS
    assert ".task-header, .task-content { max-width: min(1280px, calc(100vw - 56px)); }" in TASKS
