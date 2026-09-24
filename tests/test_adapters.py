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


def test_plan_adapter_preserves_sections_tasks_and_nested_groups():
    source = {
        "id": 7,
        "name": "Nested plan",
        "date": [2026, 9, 25],
        "sections": [{
            "letter": "A",
            "name": "第一阶段",
            "tasks": [{"internal_id": "A1", "display_id": "A1", "content": "基础任务"}],
            "groups": {
                "0_5": {"title": "阶段总组", "description": "外层"},
                "1_2": {"title": "嵌套组", "description": "内层"},
            },
        }],
    }

    unified = PlanAdapter.to_unified_plan(source)

    assert unified.sections[0]["tasks"][0]["internal_id"] == "A1"
    assert unified.sections[0]["groups"]["0_5"]["title"] == "阶段总组"
    assert unified.sections[0]["groups"]["1_2"]["title"] == "嵌套组"
