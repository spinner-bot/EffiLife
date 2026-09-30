from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plan-helper"))

from modules import api
from modules.plan import Plan


ROOT = Path(__file__).resolve().parents[1]
SEARCH = (ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue").read_text(encoding="utf-8")
GATEWAY = (ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts").read_text(encoding="utf-8")
API = (ROOT / "plan-helper" / "modules" / "api.py").read_text(encoding="utf-8")


def test_archived_plan_tasks_are_searchable_with_exact_archive_context():
    assert "plan.tasks || []" in SEARCH
    assert "archive=${encodeURIComponent(plan.file)}&task=" in SEARCH
    assert "tasks?: PlanTaskSummary[]" in GATEWAY
    assert "_serialize_raw_archive_tasks" in API
    assert '"tasks": _serialize_raw_archive_tasks(plan_data)' in API


def test_archive_summary_projects_active_task_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("EFFILIFE_PLAN_ARCHIVE_DIR", str(tmp_path / "archives"))
    plan_id = Plan.request_id()
    created = api.create_plan(name="Search archive", plan_id=plan_id)
    assert created.success
    plan = Plan.registry[plan_id]
    plan.add_section("Section", "")
    plan.add_plan(0, "Find me", 2)
    archive = api.archive_plan(plan_id)
    assert archive.success
    try:
        listed = api.list_archives()
        tasks = listed.data["archives"][0]["tasks"]
        assert tasks[0]["content"] == "Find me"
        assert tasks[0]["display_id"] == "A1"
        assert tasks[0]["internal_id"] == "A1"
    finally:
        Plan.registry.pop(plan_id, None)
