from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_HUB = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_hub_compacts_task_actions_before_desktop_two_column_breakpoint():
    source = PLAN_HUB.read_text(encoding="utf-8")
    assert "@media (max-width: 1099px)" in source
    assert "The two-column detail workspace starts at 1100px" in source
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; }" in source

