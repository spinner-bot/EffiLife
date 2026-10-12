from pathlib import Path


ROOT = Path(__file__).parents[1]
APP = (ROOT / "time-helper/desk/src/App.vue").read_text(encoding="utf-8")
ROUTER = (ROOT / "time-helper/desk/src/router/index.ts").read_text(encoding="utf-8")
HOME = (ROOT / "time-helper/desk/src/views/HomeView.vue").read_text(encoding="utf-8")
SETTINGS = (ROOT / "time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")


def test_hotl_keeps_ph_and_td_as_separate_workspaces():
    assert "path: '/plans'" in ROUTER
    assert "path: '/tasks'" in ROUTER
    assert "router.push('/plans')" in HOME
    assert "router.push('/tasks')" in HOME
    assert 'class="module-switcher-link"' in PLANS
    assert 'class="module-switcher-link"' in TASKS


def test_hotl_keeps_time_and_event_plan_workflows_complementary():
    assert "router.push('/time')" in HOME
    assert "router.push({ path: '/plans', query: { plan: plan.id } })" in HOME
    assert "recordLinkedTodoTime" in PLANS
    assert "path: '/records', query: { todo: linkedTodo.id }" in PLANS


def test_hotl_has_no_active_standalone_calendar_entry():
    assert 'to="/calendar"' not in APP
    assert "t('nav.calendar')" not in APP
    assert "path: '/calendar'" in ROUTER  # legacy bookmarks remain redirectable


def test_hotl_theme_exit_is_confirmed_and_has_no_save_button():
    theme_view = SETTINGS.split("currentView === 'theme'", 1)[1].split("currentView === 'help'", 1)[0]
    assert "requestConfirm(t('settings.theme.unsavedConfirm'))" in SETTINGS
    assert "return await confirmThemeExit()" in SETTINGS
    assert 'type="submit"' not in theme_view


def test_hotl_desktop_home_is_a_wide_two_column_console():
    assert "@media (min-width: 900px)" in HOME
    desktop = HOME.split("@media (min-width: 900px)", 1)[1]
    assert "grid-template-columns: minmax(220px, .58fr) minmax(0, 1.42fr)" in desktop
    assert "max-width: 1180px" in desktop
