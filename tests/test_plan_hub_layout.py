from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_HUB = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_hub_keeps_tablet_task_rows_horizontal_before_mobile_breakpoint():
    source = PLAN_HUB.read_text(encoding="utf-8")
    assert "@media (max-width: 1099px)" in source
    assert "The two-column detail workspace starts at 1100px" in source
    assert "Tablet keeps the task" in source
    assert "@media (min-width: 761px) and (max-width: 1099px)" in source
    assert ".event-task-row { grid-template-columns: 24px minmax(120px, 1fr) auto 58px auto 58px 28px 28px;" in source
