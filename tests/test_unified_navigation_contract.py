from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_unified_shell_exposes_the_time_helper_calendar_route():
    assert "to=\"/calendar\"" in APP
    assert "route.path.startsWith('/calendar')" in APP
    assert "t('nav.calendar')" in APP


def test_unified_shell_updates_document_title_for_route_and_locale():
    assert "const pageTitle = computed(() =>" in APP
    assert "watch([() => route.path, locale]" in APP
    assert "document.title = `${pageTitle.value} · EffiLife`" in APP
    assert "path.startsWith('/tasks')" in APP
    assert "path.startsWith('/day')" in APP
