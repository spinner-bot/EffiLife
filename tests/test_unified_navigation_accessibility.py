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


def test_desktop_shell_provides_fast_workspace_switching_shortcuts():
    assert "const router = useRouter()" in APP
    assert "event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey" in APP
    assert "'1': '/'," in APP
    assert "'2': '/plans'," in APP
    assert "'3': '/time'," in APP
    assert "'4': '/tasks'," in APP
    assert "'5': '/records'," in APP
    assert "void router.push(target)" in APP
    assert "!isEditableTarget(event.target)" in APP


def test_desktop_navigation_discloses_workspace_shortcuts():
    for shortcut in ("aria-keyshortcuts=\"Alt+1\"", "aria-keyshortcuts=\"Alt+2\"", "aria-keyshortcuts=\"Alt+3\"", "aria-keyshortcuts=\"Alt+4\"", "aria-keyshortcuts=\"Alt+5\""):
        assert shortcut in APP
    assert 'class="global-nav-shortcut" aria-hidden="true">Alt 1</kbd>' in APP
    assert 'class="global-nav-shortcut" aria-hidden="true">Alt 5</kbd>' in APP
    assert ".global-nav-shortcut { display: none; }" in APP


def test_mobile_navigation_keeps_records_as_a_first_class_sixth_entry():
    assert 'data-guide="records" to="/records"' in APP
    assert 'grid-template-columns: repeat(6, minmax(44px, 1fr));' in APP
    assert 'overflow-x: auto;' in APP
