from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_desktop_and_mobile_navigation_expose_current_page_semantics():
    assert APP.count(':aria-current="route.path === \'/\' ? \'page\' : undefined"') == 2
    assert APP.count(":aria-current=\"route.path.startsWith('/plans') || route.path === '/plan' ? 'page' : undefined\"") == 2
    assert APP.count(":aria-current=\"route.path.startsWith('/time') ? 'page' : undefined\"") == 2
    assert APP.count(":aria-current=\"route.path.startsWith('/records') || route.path.startsWith('/day') ? 'page' : undefined\"") == 2
    assert APP.count(":aria-current=\"route.path.startsWith('/tasks') ? 'page' : undefined\"") == 2
    assert APP.count(':aria-current="isSettingsRoute ? \'page\' : undefined"') == 2


def test_global_search_button_declares_supported_shortcuts():
    assert 'aria-keyshortcuts="Control+K Meta+K"' in APP


def test_mobile_navigation_keeps_records_as_a_first_class_sixth_entry():
    assert 'data-guide="records" to="/records"' in APP
    assert 'grid-template-columns: repeat(6, minmax(0, 1fr));' in APP
