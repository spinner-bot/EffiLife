import pytest

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


def test_todo_adapter_keeps_stable_plan_task_reference():
    from common.api_gateway.adapters import TodoAdapter

    todo = TodoAdapter.to_unified_todo({
        "id": "TODO-1",
        "title": "写报告",
        "related_plan_id": "7",
        "related_plan_task_id": "A3",
    })

    assert todo.related_plan_id == "7"
    assert todo.related_plan_task_id == "A3"
    assert TodoAdapter.from_unified_todo(todo)["related_plan_task_id"] == "A3"


def test_todo_adapter_preserves_advanced_fields_roundtrip():
    from common.api_gateway.adapters import TodoAdapter

    source = {
        "id": "TODO-FULL",
        "title": "完整待办",
        "priority": "urgent-important",
        "priority_rank": 2,
        "urgent": True,
        "important": True,
        "start_time": "2026-09-25T09:00:00",
        "estimated_time": 45,
        "related_time_record_ids": ["TR-1", "TR-2"],
        "subtasks": [{"id": "SUB-1", "title": "子项", "completed": False}],
    }

    unified = TodoAdapter.to_unified_todo(source)
    restored = TodoAdapter.from_unified_todo(unified)

    for key in ("priority_rank", "urgent", "important", "start_time", "estimated_time", "related_time_record_ids", "subtasks"):
        assert restored[key] == source[key]


def test_legacy_todo_migration_accepts_wrapped_and_raw_payloads():
    from common.migrations.todos import migrate_legacy_todos

    todo = {"id": "TODO-1", "title": "迁移任务", "subtasks": [{"id": "SUB-1", "title": "子项"}]}
    wrapped = migrate_legacy_todos({"version": "0.3.0", "todos": [todo], "categories": [{"id": "work", "name": "工作"}]})
    raw = migrate_legacy_todos([todo])

    assert wrapped["source_version"] == "0.3.0"
    assert wrapped["categories"][0]["id"] == "work"
    assert wrapped["categories"][0]["name"] == "工作"
    assert wrapped["categories"][0]["module"] == "to-dos"
    assert wrapped["todos"][0]["subtasks"] == todo["subtasks"]
    assert raw["source_version"] is None


def test_legacy_todo_migration_strict_and_lenient_errors():
    from common.migrations.todos import TodoMigrationError, migrate_legacy_todos

    invalid = [{"id": "TODO-1", "title": "有效"}, {"title": "缺少 id"}]
    try:
        migrate_legacy_todos(invalid)
    except TodoMigrationError as error:
        assert "缺少 id" in str(error)
    else:
        raise AssertionError("strict migration should reject invalid entries")

    result = migrate_legacy_todos(invalid, strict=False)
    assert len(result["todos"]) == 1
    assert len(result["warnings"]) == 1


def test_legacy_todo_migration_rejects_invalid_categories_consistently():
    from common.migrations.todos import TodoMigrationError, migrate_legacy_todos

    with pytest.raises(TodoMigrationError, match="分类第 0 项缺少 name"):
        migrate_legacy_todos({"todos": [], "categories": [{"id": "work"}]})

    result = migrate_legacy_todos({"todos": [], "categories": [{"id": "work"}]}, strict=False)
    assert result["categories"] == []
    assert result["warnings"] == ["分类第 0 项缺少 name"]


def test_time_adapter_accepts_unified_frontend_record_fields():
    from common.api_gateway.adapters import TimeAdapter

    record = TimeAdapter.to_unified_record({
        "id": "TR-1",
        "date": "2026-09-25",
        "start": "09:00",
        "end": "10:30",
        "duration": 1.5,
        "content": "统一任务",
        "tag": "work",
        "todo_id": "TODO-1",
    })

    assert record.id == "TR-1"
    assert record.date == "2026-09-25"
    assert record.duration_hours == 1.5
    assert record.related_todo_id == "TODO-1"
    restored = TimeAdapter.from_unified_record(record)
    assert restored["id"] == "TR-1"
    assert restored["todo_id"] == "TODO-1"
    assert restored["start"] == "09:00"


def test_unified_category_preserves_difficulty():
    from common.api_gateway.adapters import CategoryAdapter
    from common.schemas.models import UnifiedCategory

    category = CategoryAdapter.to_unified_category({"id": "work", "name": "工作", "difficulty": 8})

    assert UnifiedCategory.from_dict(category.to_dict()).difficulty == 8
    assert CategoryAdapter.from_unified_category(category)["difficulty"] == 8
