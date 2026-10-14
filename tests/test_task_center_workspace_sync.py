from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_center_refreshes_when_plan_workspace_changes():
    expected = "['todos', 'plans', 'records', 'settings', 'archive', 'network']"
    assert TASKS.count(expected) == 2
