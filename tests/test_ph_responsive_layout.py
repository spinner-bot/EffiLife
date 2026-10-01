from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_task_actions_remain_horizontal_on_tablet_and_stack_on_mobile():
    source = SOURCE.read_text(encoding="utf-8")
    assert "@media (max-width: 1099px)" in source
    tablet_block = source.split("@media (min-width: 761px) and (max-width: 1099px)", 1)[1].split("@media (max-width: 760px)", 1)[0]
    mobile_block = source.split("@media (max-width: 760px)", 1)[1]
    assert ".event-task-row { grid-template-columns: 24px minmax(120px, 1fr) auto 58px auto 58px 28px 28px;" in tablet_block
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; }" in mobile_block
    assert ".event-task-row .task-log" in mobile_block
