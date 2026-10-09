from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POPUP = ROOT / "time-helper" / "desk" / "src" / "audio" / "EventPopup.vue"


def test_event_popup_auto_dismiss_matches_visible_progress_duration():
    source = POPUP.read_text(encoding="utf-8")
    assert "const AUTO_DISMISS_MS = 5000" in source
    assert "setTimeout(() =>" in source
    assert "EventSystem.dismissEvent(event.id)" in source
    assert "watch(events" in source


def test_event_popup_cleans_manual_and_unmount_timers():
    source = POPUP.read_text(encoding="utf-8")
    assert "clearTimeout(timer)" in source
    assert "onBeforeUnmount(() =>" in source
    assert "dismissTimers.clear()" in source
    assert "dismissTimers.delete(eventId)" in source
