from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
TIME = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_home_uses_wide_desktop_console_layout():
    assert "@media (min-width: 900px)" in HOME
    assert "max-width: 1180px" in HOME
    assert "grid-template-columns: minmax(150px, 190px) minmax(0, 1fr)" in HOME


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
