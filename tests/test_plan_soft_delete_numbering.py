from pathlib import Path
import sys


PLAN_HELPER_DIR = Path(__file__).resolve().parents[1] / "plan-helper"
sys.path.insert(0, str(PLAN_HELPER_DIR))

from modules import api  # noqa: E402
from modules.plan import Plan  # noqa: E402


def test_soft_delete_compacts_display_ids_without_rewriting_internal_slots_or_nested_groups():
    Plan.registry.clear()


def test_new_log_resolves_display_id_to_stable_internal_id_after_soft_delete():
    Plan.registry.clear()
    created = api.create_plan(
        name="Stable log references",
        sections=[{
            "name": "Section A",
            "tasks": [
                {"content": "A1", "time_minutes": 10},
                {"content": "A2", "time_minutes": 10},
                {"content": "A3", "time_minutes": 10},
            ],
        }],
    )
    assert created.success
    plan_id = created.data["id"]

    assert api.delete_task(plan_id, "A2").success
    response = api.add_log(plan_id, day=1, task_id="A2", time_input=(9, 30), content="继续推进")
    assert response.success
    assert response.data["task_id"] == "A2"
    assert response.data["resolved_task_id"] == "A3"
    assert Plan.registry[plan_id].plan["log"][0]["plan"] == "A3"

    Plan.registry.clear()
    created = api.create_plan(
        name="Numbering contract",
        date_tuple=(2026, 10, 1),
        sections=[{
            "name": "Section A",
            "tasks": [
                {"content": "A1", "time_minutes": 10},
                {"content": "A2", "time_minutes": 10},
                {"content": "A3", "time_minutes": 10},
            ],
        }],
    )
    assert created.success
    plan_id = created.data["id"]

    assert api.add_group(plan_id, 0, "Outer", start_index=1, end_index=3).success
    assert api.add_group(plan_id, 0, "Inner", start_index=1, end_index=2).success
    assert api.add_log(plan_id, day=1, task_id="A2", time_input=(9, 30), content="historical work").success
    assert api.delete_task(plan_id, "A2").success

    full = api.get_plan_full(plan_id)
    assert full.success
    tasks = full.data["sections"][0]["tasks"]
    assert [(task["display_id"], task["internal_id"], task["content"]) for task in tasks] == [
        ("A1", "A1", "A1"),
        ("A2", "A3", "A3"),
    ]
    assert set(full.data["sections"][0]["groups"]) == {"1_3", "1_2"}
    assert full.data["logs"][0]["plan"] == "A2"
    assert full.data["logs"][0]["content"] == "historical work"

    Plan.registry.clear()
