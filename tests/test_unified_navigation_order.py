from pathlib import Path


SOURCE = Path("time-helper/desk/src/App.vue").read_text(encoding="utf-8")


def test_desktop_navigation_order_matches_keyboard_shortcuts_and_mobile_navigation():
    desktop = SOURCE[SOURCE.index('<nav class="global-nav-links'):SOURCE.index('</nav>', SOURCE.index('<nav class="global-nav-links'))]

    assert desktop.index('data-guide="tasks"') < desktop.index('data-guide="records"')
    assert desktop.index('aria-keyshortcuts="Alt+4"') < desktop.index('aria-keyshortcuts="Alt+5"')


def test_tasks_and_records_remain_independent_routes_in_the_shell():
    assert 'to="/tasks"' in SOURCE
    assert 'to="/records"' in SOURCE
    assert 'data-guide="tasks"' in SOURCE
    assert 'data-guide="records"' in SOURCE
