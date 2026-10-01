from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEWS = ROOT / "time-helper" / "desk" / "src" / "views"
HOME = (VIEWS / "HomeView.vue").read_text(encoding="utf-8")
TIME = (VIEWS / "PlanView.vue").read_text(encoding="utf-8")
SETTINGS = (VIEWS / "SettingsView.vue").read_text(encoding="utf-8")


def test_home_uses_wide_desktop_console_layout():
    assert "@media (min-width: 900px)" in HOME
    assert "max-width: 1180px" in HOME
    assert "grid-template-columns: minmax(150px, 190px) minmax(0, 1fr)" in HOME


def test_home_inbox_panel_stays_inside_narrow_mobile_viewports():
    assert "width: min(360px, calc(100vw - 32px));" in HOME
    assert "max-width: calc(100vw - 32px);" in HOME


def test_app_keeps_tablet_navigation_horizontal_without_overflowing_controls():
    app = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
    assert "@media (min-width: 681px) and (max-width: 820px)" in app
    tablet_block = app.split("@media (min-width: 681px) and (max-width: 820px)", 1)[1].split("/* ", 1)[0]
    assert ".global-nav-link { gap: 4px; padding: 7px 6px; font-size: 11px; }" in tablet_block
    assert ".global-search-trigger span, .global-search-trigger kbd { display: none; }" in tablet_block


def test_mobile_navigation_keeps_touch_targets_without_hiding_module_entries():
    app = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
    mobile_block = app.split("@media (max-width: 680px)", 1)[1]
    assert "grid-template-columns: repeat(6, minmax(44px, 1fr));" in mobile_block
    assert "overflow-x: auto;" in mobile_block
    assert "scrollbar-width: none;" in mobile_block


def test_time_workspace_has_a_wide_screen_content_budget():
    assert "@media (min-width: 1100px)" in TIME
    assert "max-width: 1180px" in TIME


def test_settings_uses_two_column_desktop_navigation():
    assert "@media (min-width: 900px)" in SETTINGS
    assert "max-width: 920px" in SETTINGS
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in SETTINGS


def test_settings_archive_actions_use_horizontal_desktop_layout_and_mobile_stack():
    assert ".archive-actions {" in SETTINGS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in SETTINGS
    mobile_block = SETTINGS.split("@media (max-width: 680px)", 1)[1]
    assert ".archive-actions { display: flex; flex-direction: column; }" in mobile_block


def test_task_center_uses_the_shared_wide_desktop_content_budget():
    tasks = (VIEWS / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "@media (min-width: 1100px)" in tasks
    assert ".task-header, .task-content { max-width: 1180px; }" in tasks


def test_task_center_only_stacks_editing_controls_on_mobile():
    tasks = (VIEWS / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "@media (max-width: 700px)" in tasks
    mobile_block = tasks.split("@media (max-width: 700px)", 1)[1]
    assert ".task-edit-form { grid-template-columns: 1fr; }" in mobile_block
    assert ".task-item-actions { flex-basis: 100%;" in mobile_block
    assert "@media (max-width: 1099px)" not in tasks


def test_task_center_toolbar_wraps_module_controls_without_overlap():
    tasks = (VIEWS / "TaskCenterView.vue").read_text(encoding="utf-8")
    toolbar = tasks.split(".task-toolbar {", 1)[1].split("}", 1)[0]
    assert "flex-wrap: wrap" in toolbar
    assert "gap: 10px" in toolbar
    tabs = tasks.split(".task-tabs {", 1)[1].split("}", 1)[0]
    assert "max-width: 100%" in tabs
    assert "overflow-x: auto" in tabs


def test_plan_detail_actions_wrap_before_the_mobile_breakpoint():
    plans = (VIEWS / "PlansHubView.vue").read_text(encoding="utf-8")
    assert ".detail-toolbar { display: flex; flex-wrap: wrap;" in plans
    assert ".detail-actions { display: flex; flex-wrap: wrap;" in plans
    assert ".plan-section > header { display: flex; flex-wrap: wrap;" in plans
    assert "@media (max-width: 1099px)" in plans


def test_plan_detail_uses_a_desktop_summary_sidebar_and_mobile_single_column():
    plans = (VIEWS / "PlansHubView.vue").read_text(encoding="utf-8")
    assert 'class="plan-detail-layout"' in plans
    assert 'class="plan-detail-aside"' in plans
    assert 'class="plan-detail-main"' in plans
    desktop_block = plans.split("@media (min-width: 1100px)", 1)[1]
    assert ".plan-detail-layout { grid-template-columns: minmax(250px, .34fr) minmax(0, 1fr);" in desktop_block


def test_home_uses_a_wide_dashboard_at_desktop_breakpoint():
    source = (VIEWS / "HomeView.vue").read_text(encoding="utf-8")
    desktop = source.split("@media (min-width: 900px)", 1)[1]
    assert ".main-content" in desktop
    assert "max-width: 1180px" in desktop
    assert "grid-template-columns: minmax(150px, 190px) minmax(0, 1fr)" in desktop


def test_core_workspaces_expand_beyond_mobile_card_width_on_desktop():
    sources = {
        "plans": ((VIEWS / "PlansHubView.vue").read_text(encoding="utf-8"), "max-width: 1080px"),
        "tasks": ((VIEWS / "TaskCenterView.vue").read_text(encoding="utf-8"), "max-width: 1180px"),
        "records": ((VIEWS / "RecordsView.vue").read_text(encoding="utf-8"), "max-width: 1180px"),
    }
    for source, expected_width in sources.values():
        assert expected_width in source
        assert "@media (min-width: 1100px)" in source


def test_records_view_activates_grid_before_declaring_desktop_columns():
    records = (VIEWS / "RecordsView.vue").read_text(encoding="utf-8")
    assert ".records-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: start; }" in records


def test_records_form_prevents_mobile_input_overflow():
    records = (VIEWS / "RecordsView.vue").read_text(encoding="utf-8")
    assert ".modal {" in records and "box-sizing: border-box;" in records
    assert ".time-input-row {" in records and "flex-wrap: wrap;" in records
    assert ".text-input, .select-input {" in records
    assert "box-sizing: border-box;" in records


def test_desktop_workspaces_keep_mobile_breakpoints_explicit():
    for name in ("PlansHubView.vue", "TaskCenterView.vue", "RecordsView.vue"):
        source = (VIEWS / name).read_text(encoding="utf-8")
        assert "@media (max-width: 760px)" in source or "@media (max-width: 700px)" in source or "@media (max-width: 680px)" in source
