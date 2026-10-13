from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"


def test_home_surfaces_active_focus_session_and_resume_action():
    source = HOME.read_text(encoding="utf-8")

    assert "FocusSessionService.onChange" in source
    assert "activeFocusSession" in source
    assert "home.resumeFocus" in source
    assert "query: { todo: session.todoId }" in source


def test_home_focus_banner_has_mobile_layout_and_live_status():
    source = HOME.read_text(encoding="utf-8")

    assert 'class="active-focus-banner theme-card" aria-live="polite"' in source
    assert ".active-focus-banner { align-items: stretch; flex-direction: column; }" in source
