from common.api_gateway.adapters import PlanAdapter


def test_plan_adapter_normalizes_date_and_task_ids():
    plan = PlanAdapter.to_unified_plan({
        "id": 3,
        "name": "Today",
        "date": [2026, 9, 5],
    })
    assert plan.date == "2026-09-05"

    task_ids = PlanAdapter.extract_task_ids({
        "sections": [{
            "letter": "A",
            "tasks": [
                {"internal_id": "A1", "content": "First", "is_active": True},
                {"internal_id": "A2", "content": "Deleted", "is_active": False},
            ],
        }]
    })
    assert task_ids == ["A1"]
