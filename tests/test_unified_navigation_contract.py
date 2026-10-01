from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
ROUTER = (ROOT / "time-helper" / "desk" / "src" / "router" / "index.ts").read_text(encoding="utf-8")


def test_unified_shell_removes_standalone_calendar_entry_but_keeps_legacy_redirect():
    assert 'to="/calendar"' not in APP
    assert "route.path.startsWith('/calendar')" not in APP
    assert "t('nav.calendar')" not in APP
    assert "path: '/calendar'" in ROUTER
    assert "redirect: '/records'" in ROUTER


def test_legacy_management_route_redirects_to_time_workspace():
    assert "path: '/management'" in ROUTER
    assert "redirect: '/time'" in ROUTER
    assert "component: () => import('@/views/ManagementView.vue')" not in ROUTER


def test_unified_shell_updates_document_title_for_route_and_locale():
    assert "const pageTitle = computed(() =>" in APP
    assert "watch([() => route.path, locale]" in APP
    assert "document.title = t('app.documentTitle', { page: pageTitle.value })" in APP
    assert "'app.documentTitle': '{page} · EffiLife'" in (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_html_bootstrap_title_uses_unified_product_brand():
    html = (ROOT / "time-helper" / "desk" / "index.html").read_text(encoding="utf-8")
    assert "<title>EffiLife</title>" in html
    assert "浪兮效率时钟" not in html
    assert "path.startsWith('/tasks')" in APP
    assert "path.startsWith('/time')" in APP
    assert "path.startsWith('/day')" in APP


def test_settings_subroutes_keep_the_settings_navigation_entry_active():
    assert "const isSettingsRoute = computed(() => ['/settings', '/audio-settings', '/motion-settings', '/event-manager'].includes(route.path))" in APP
    assert ":class=\"{ active: isSettingsRoute }\"" in APP
