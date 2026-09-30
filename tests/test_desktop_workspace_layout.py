from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
TIME = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_home_uses_wide_desktop_console_layout():
    assert "@media (min-width: 900px)" in HOME
    assert "max-width: 1180px" in HOME
    assert "grid-template-columns: minmax(150px, 190px) minmax(0, 1fr)" in HOME


def test_app_keeps_tablet_navigation_horizontal_without_overflowing_controls():
    app = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
    assert "@media (min-width: 681px) and (max-width: 820px)" in app
    tablet_block = app.split("@media (min-width: 681px) and (max-width: 820px)", 1)[1].split("/* ", 1)[0]
    assert ".global-nav-link { gap: 4px; padding: 7px 6px; font-size: 11px; }" in tablet_block
    assert ".global-search-trigger span, .global-search-trigger kbd { display: none; }" in tablet_block


def test_time_workspace_has_a_wide_screen_content_budget():
    assert "@media (min-width: 1100px)" in TIME
    assert "max-width: 1180px" in TIME


def test_settings_uses_two_column_desktop_navigation():
    assert "@media (min-width: 900px)" in SETTINGS
    assert "max-width: 920px" in SETTINGS
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in SETTINGS


def test_task_center_uses_the_shared_wide_desktop_content_budget():
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "@media (min-width: 1100px)" in tasks
    assert ".task-header, .task-content { max-width: 1180px; }" in tasks


def test_plan_detail_actions_wrap_before_the_mobile_breakpoint():
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert ".detail-toolbar { display: flex; flex-wrap: wrap;" in plans
    assert ".detail-actions { display: flex; flex-wrap: wrap;" in plans
    assert ".plan-section > header { display: flex; flex-wrap: wrap;" in plans
    assert "@media (max-width: 900px)" in plans
