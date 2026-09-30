from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_task_actions_collapse_before_tablet_width():
    source = SOURCE.read_text(encoding="utf-8")
    assert "@media (max-width: 1099px)" in source
    responsive_block = source.split("@media (max-width: 1099px)", 1)[1].split("@media (prefers-reduced-motion", 1)[0]
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; }" in responsive_block
    assert ".event-task-row .task-log" in responsive_block
    assert ".event-task-row .task-edit" in responsive_block
