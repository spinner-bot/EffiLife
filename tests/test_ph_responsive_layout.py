from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"


def test_plan_task_actions_remain_horizontal_on_tablet_and_stack_on_mobile():
    source = SOURCE.read_text(encoding="utf-8")
    assert "@media (max-width: 1099px)" in source
    tablet_block = source.split("@media (min-width: 761px) and (max-width: 1099px)", 1)[1].split("@media (max-width: 760px)", 1)[0]
    mobile_block = source.split("@media (max-width: 760px)", 1)[1]
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; gap: 7px; }" in tablet_block
    assert ".event-task-actions { grid-column: 2 / -1; justify-content: flex-start; flex-wrap: wrap; }" in tablet_block
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; }" in mobile_block
    assert ".event-task-actions { grid-column: 2 / -1; grid-row: 3;" in mobile_block


def test_plan_task_mobile_grid_assigns_every_action_without_implicit_columns():
    source = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    mobile_block = source.split("@media (max-width: 760px)", 1)[1]
    assert ".event-task-row { grid-template-columns: 24px minmax(0, 1fr) auto; }" in mobile_block
    assert ".event-task-actions { grid-column: 2 / -1; grid-row: 3;" in mobile_block


def test_group_editor_uses_two_columns_on_tablet_and_one_on_mobile():
    source = SOURCE.read_text(encoding="utf-8")
    tablet_block = source.split("@media (min-width: 761px) and (max-width: 1099px)", 1)[1].split("@media (max-width: 760px)", 1)[0]
    mobile_block = source.split("@media (max-width: 760px)", 1)[1]
    assert ".group-editor { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: end; }" in tablet_block
    assert ".group-editor label:nth-child(1), .group-editor label:nth-child(2) { grid-column: 1 / -1; }" in tablet_block
    assert ".group-editor { grid-template-columns: 1fr; }" in mobile_block
    assert ".group-editor button { width: 100%; }" in mobile_block


def test_plan_index_uses_activity_and_archive_columns_on_wide_desktop():
    source = SOURCE.read_text(encoding="utf-8")
    assert 'class="plan-index-layout"' in source
    assert 'class="plan-index-main"' in source
    assert ".plan-index-layout { grid-template-columns: minmax(0, 1.55fr) minmax(280px, .65fr); align-items: start; }" in source
    assert ".plan-index-main .event-plan-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }" in source
