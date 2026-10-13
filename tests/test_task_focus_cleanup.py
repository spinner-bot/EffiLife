from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_focus_cleanup_keeps_session_alive_across_route_changes():
    cleanup = TASKS.split("onUnmounted(() =>", 1)[1].split("watch(selectedPlanId", 1)[0]
    assert "The session belongs to the workspace shell now" in cleanup
    assert "clearFocusTimer()" in cleanup
    assert "void stopFocus(activeFocusTodo).catch((error) =>" not in cleanup

