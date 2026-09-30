from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_CENTER = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_center_does_not_use_a_global_task_id_map_across_plans():
    assert "#{{ todo.related_plan_task_id }}" in TASK_CENTER
    assert "planTaskById[todo.related_plan_task_id]" not in TASK_CENTER
    assert "task: todo.related_plan_task_id" in TASK_CENTER
