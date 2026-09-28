from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_CENTER = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_center_resolves_internal_and_display_plan_task_ids():
    assert "[task.internal_id, task]" in TASK_CENTER
    assert "[task.display_id, task]" in TASK_CENTER
