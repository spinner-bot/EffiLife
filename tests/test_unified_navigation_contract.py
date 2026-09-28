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


def test_unified_shell_updates_document_title_for_route_and_locale():
    assert "const pageTitle = computed(() =>" in APP
    assert "watch([() => route.path, locale]" in APP
    assert "document.title = `${pageTitle.value} · EffiLife`" in APP
    assert "path.startsWith('/tasks')" in APP
    assert "path.startsWith('/day')" in APP
