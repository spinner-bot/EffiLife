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


def test_mobile_navigation_matches_desktop_task_and_record_order():
    mobile = APP.split('<nav class="mobile-bottom-nav', 1)[1].split('</nav>', 1)[0]
    assert mobile.index('data-guide="tasks"') < mobile.index('data-guide="records"')


def test_unified_shell_exposes_a_localized_skip_link_and_main_landmark():
    assert 'href="#main-content"' in APP
    assert "t('app.skipToContent')" in APP
    assert 'id="main-content"' in APP
    assert 'class="app-main"' in APP
    assert 'tabindex="-1"' in APP


def test_route_changes_move_focus_to_main_content_without_query_churn():
    assert "const mainContent = ref<HTMLElement | null>(null)" in APP
    assert "watch(() => route.path, async (path, previousPath)" in APP
    assert "if (!runtimeReady.value || path === previousPath) return" in APP
    assert "mainContent.value?.focus({ preventScroll: true })" in APP
