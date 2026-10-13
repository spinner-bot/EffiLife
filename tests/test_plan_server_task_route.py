from pathlib import Path


SERVER = (Path(__file__).resolve().parents[1] / "plan-helper" / "web" / "server.py").read_text(encoding="utf-8")


def test_plan_task_list_route_extracts_plan_id_segment():
    """The REST route must pass {plan_id}, not the literal `plans` segment."""
    assert 'path.endswith("/tasks")' in SERVER
    assert 'plan_id = parts[3]' in SERVER
    assert 'plan_id = parts[2]' not in SERVER
