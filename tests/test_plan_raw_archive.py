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


def test_registry_exchange_round_trip_preserves_archived_plan_payloads(tmp_path, monkeypatch):
    monkeypatch.setenv("EFFILIFE_PLAN_ARCHIVE_DIR", str(tmp_path / "archives"))
    plan_id = Plan.request_id()
    created = api.create_plan(name="Archived exchange", plan_id=plan_id)
    assert created.success
    try:
        archived = api.archive_plan(plan_id)
        assert archived.success
        exported = api.export_registry()
        assert exported.success
        assert exported.data["plans"] == []
        assert len(exported.data["archives"]) == 1

        imported = api.import_registry(
            exported.data["plans"],
            archives=exported.data["archives"],
            replace=True,
        )
        assert imported.success
        listed = api.list_archives()
        assert listed.success
        assert listed.data["count"] == 1
        assert listed.data["archives"][0]["name"] == "Archived exchange"
    finally:
        Plan.registry.pop(plan_id, None)


def test_repeated_archive_restore_does_not_overwrite_history(tmp_path, monkeypatch):
    archive_dir = tmp_path / "archives"
    monkeypatch.setenv("EFFILIFE_PLAN_ARCHIVE_DIR", str(archive_dir))
    plan_id = Plan.request_id()
    created = api.create_plan(name="Archive history", plan_id=plan_id)
    assert created.success
    try:
        first = api.archive_plan(plan_id)
        assert first.success
        first_file = Path(first.data["file"])
        restored = api.restore_archive(first_file.name)
        assert restored.success
        second = api.archive_plan(plan_id)
        assert second.success
        assert Path(second.data["file"]).name != first_file.name
        assert len(list(archive_dir.glob("plan_*.json"))) == 2
    finally:
        Plan.registry.pop(plan_id, None)


def test_archive_restore_allocates_a_new_id_when_historical_id_is_occupied(tmp_path, monkeypatch):
    archive_dir = tmp_path / "archives"
    monkeypatch.setenv("EFFILIFE_PLAN_ARCHIVE_DIR", str(archive_dir))
    original_id = Plan.request_id()
    created = api.create_plan(name="Occupied archive", plan_id=original_id)
    assert created.success
    restored_id = None
    try:
        archived = api.archive_plan(original_id)
        assert archived.success
        replacement = api.create_plan(name="Replacement", plan_id=original_id)
        assert replacement.success
        restored = api.restore_archive(Path(archived.data["file"]).name)
        assert restored.success
        restored_id = restored.data["id"]
        assert restored_id != original_id
        assert restored.data["name"] == "Occupied archive"
    finally:
        Plan.registry.pop(original_id, None)
        if restored_id is not None:
            Plan.registry.pop(restored_id, None)


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


def test_hard_deleted_log_preserves_date_and_content_of_remaining_entries():
    plan_id = Plan.request_id()
    created = api.create_plan(name="Log deletion", plan_id=plan_id)
    assert created.success
    plan = Plan.registry[plan_id]
    plan.add_section("阶段", "说明")
    plan.add_plan(0, "任务", 2)
    plan.add_log(1, "A1", (10, 20), "保留日志", date="2026-09-28")
    plan.add_log(2, "A1", (11, 30), "删除日志", date="2026-09-29")

    try:
        removed = plan.pur_log(1)
        assert len(removed) == 1
        assert plan.plan["log"] == [{
            "day": 1,
            "plan": "A1",
            "time": (10, 20),
            "content": "保留日志",
            "date": "2026-09-28",
        }]
    finally:
        Plan.registry.pop(plan_id, None)
