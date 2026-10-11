from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper/desk/src/App.vue").read_text(encoding="utf-8")


def test_desktop_navigation_marks_th_ph_and_td_as_separate_modules():
    assert 'class="global-nav-module-code" aria-hidden="true">PH</span>' in APP
    assert 'class="global-nav-module-code" aria-hidden="true">TH</span>' in APP
    assert 'class="global-nav-module-code" aria-hidden="true">TD</span>' in APP


def test_mobile_navigation_keeps_th_ph_and_td_module_codes_visible():
    assert APP.count('class="mobile-nav-module-code" aria-hidden="true">PH</small>') == 1
    assert APP.count('class="mobile-nav-module-code" aria-hidden="true">TH</small>') == 1
    assert APP.count('class="mobile-nav-module-code" aria-hidden="true">TD</small>') == 1


def test_workspace_navigation_exposes_module_responsibilities_as_titles():
    assert ':title="t(\'plans.moduleDescription\')"' in APP
    assert ':title="t(\'home.timeModuleSummary\')"' in APP
    assert ':title="t(\'tasks.moduleDescription\')"' in APP


def test_global_shell_exposes_td_quick_capture_without_owning_todo_mutations():
    assert 'to="/tasks?compose=1"' in APP
    tasks = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")
    assert 'ref="newTaskInput"' in tasks
    assert "route.query.compose" in tasks


def test_plan_and_todo_workspaces_keep_explicit_context_switchers():
    plans = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
    tasks = (ROOT / "time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")
    for view, active_route in ((plans, 'to="/plans" aria-current="page"'), (tasks, 'to="/tasks" aria-current="page"')):
        assert 'class="module-switcher"' in view
        assert 'to="/time"' in view
        assert 'to="/plans"' in view
        assert 'to="/tasks"' in view
        assert active_route in view


def test_time_workspace_keeps_the_same_explicit_context_switcher():
    time_view = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")
    assert 'class="pv-module-switcher"' in time_view
    assert 'to="/time" aria-current="page"' in time_view
    assert 'to="/plans"' in time_view
    assert 'to="/tasks"' in time_view


def test_context_switcher_is_navigation_only_and_does_not_merge_module_routes():
    router = (ROOT / "time-helper/desk/src/router/index.ts").read_text(encoding="utf-8")
    assert "path: '/plans'" in router
    assert "path: '/tasks'" in router
    assert "component: () => import('@/views/PlansHubView.vue')" in router
    assert "component: () => import('@/views/TaskCenterView.vue')" in router
