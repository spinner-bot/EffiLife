from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_plan_workspace_reacts_to_reused_route_query_deep_links():
    assert "watch(() => [route.query.plan, route.query.task, route.query.archive]" in PLANS
    assert "async function revealSearchTarget(): Promise<void>" in PLANS
    assert "await revealSearchTarget()" in PLANS
    assert "if (route.query.archive) return" in PLANS


def test_task_workspace_reacts_to_reused_route_query_deep_links():
    assert "watch(() => route.query.todo" in TASKS
    assert "async function revealSearchTarget(): Promise<void>" in TASKS
    assert "document.getElementById(`todo-${targetId}`)" in TASKS
