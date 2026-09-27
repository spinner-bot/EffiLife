import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plan-helper"))

from modules import api
from modules.plan import Plan


def test_raw_plan_registry_round_trip_preserves_slots_groups_and_logs():
    plan_id = Plan.request_id()
    created = api.create_plan(name="Raw archive", plan_id=plan_id)
    assert created.success
    plan = Plan.registry[plan_id]
    plan.add_section("阶段 A", "说明")
    first = plan.add_plan(0, "第一项", 2)
    plan.add_plan(0, "第二项", 3)
    plan.add_group(0, "外层", "外层说明", 0, 3)
    plan.add_group(0, "嵌套", "嵌套说明", 1, 2)
    plan.del_plan(first)
    plan.add_log(1, "A2", (10, 99), "历史引用")
    expected = copy.deepcopy(plan.plan)
    expected_after_json = json.loads(json.dumps(expected, ensure_ascii=False))

    try:
        exported = api.export_registry()
        assert exported.success
        snapshot = exported.data["plans"][0]
        assert snapshot == expected

        Plan.registry.clear()
        imported = api.import_registry([snapshot], replace=True)
        assert imported.success
        assert Plan.registry[plan_id].plan == expected_after_json
    finally:
        Plan.registry.pop(plan_id, None)


def test_soft_deleted_task_is_renumbered_only_in_the_display_projection():
    plan_id = Plan.request_id()
    created = api.create_plan(name="Display numbering", plan_id=plan_id)
    assert created.success
    plan = Plan.registry[plan_id]
    plan.add_section("阶段 A", "说明")
    first = plan.add_plan(0, "已删除项", 2)
    plan.add_plan(0, "保留项", 3)
    plan.add_group(0, "外层", "外层说明", 0, 3)
    plan.add_group(0, "嵌套", "嵌套说明", 1, 2)
    historical_snapshot = copy.deepcopy(plan.plan)

    try:
        assert plan.del_plan(first) == first
        projected = api.get_plan_full(plan_id)
        assert projected.success
        tasks = projected.data["sections"][0]["tasks"]
        assert [task["display_id"] for task in tasks] == ["A1"]
        assert tasks[0]["content"] == "保留项"
        _, first_internal_index = Plan.sep_index(first)
        assert plan.plan["main"][0]["plan"][first_internal_index]["is_active"] is False
        assert set(plan.plan["main"][0]["group"]) == set(historical_snapshot["main"][0]["group"])
    finally:
        Plan.registry.pop(plan_id, None)
