from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_focus_cleanup_does_not_leave_an_unhandled_persistence_failure():
    cleanup = TASKS.split("onUnmounted(() =>", 1)[1].split("watch(selectedPlanId", 1)[0]
    assert "void stopFocus(activeFocusTodo).catch((error) =>" in cleanup
    assert "Failed to persist focus time during task-center cleanup:" in cleanup

