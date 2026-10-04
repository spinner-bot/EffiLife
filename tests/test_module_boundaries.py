from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper" / "desk" / "src"
PLANS = (SRC / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
TASKS = (SRC / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
HOME = (SRC / "views" / "HomeView.vue").read_text(encoding="utf-8")
RECORDS = (SRC / "views" / "RecordsView.vue").read_text(encoding="utf-8")
ROUTER = (SRC / "router" / "index.ts").read_text(encoding="utf-8")
TODO_SERVICE = (SRC / "services" / "todoService.ts").read_text(encoding="utf-8")


def test_ph_workspace_owns_plan_data_and_progress_only():
    # PH may create an explicit TD relation, but it remains the owner of
    # plan structure and progress mutations.
    assert "TodoService.create" in PLANS
    assert "related_plan_id" in PLANS
    assert "updatePlanTask" in PLANS
    assert "saveLog" in PLANS
    assert "addPlanGroup" in PLANS


def test_td_workspace_owns_todo_data_without_plan_editing_controls():
    assert "planGateway" not in TASKS
    assert "related_plan_id" not in TASKS
    assert "completePlanTask" not in TASKS
    assert "TodoService.create" in TASKS
    assert "TodoService.update" in TASKS


def test_th_records_keep_only_explicit_todo_record_association():
    assert "listPlanArchives" not in RECORDS
    assert "openLinkedPlan" not in RECORDS
    assert "openLinkedTodo" in RECORDS
    assert "unlinkTodoFromTimeRecord" in RECORDS


def test_home_is_a_dashboard_not_a_cross_module_editor():
    assert "refreshEventPlanSummary" in HOME
    assert "refreshTodoSummary" in HOME
    assert "openTodoPlan" not in HOME
    assert "todo.related_plan_id" not in HOME


def test_primary_routes_expose_three_independent_workspaces():
    for path in ("'/plans'", "'/time'", "'/tasks'", "'/records'"):
        assert f"path: {path}" in ROUTER


def test_legacy_plan_relation_fields_remain_only_for_compatibility_data():
    assert "related_plan_id?: string" in TODO_SERVICE
    assert "related_plan_task_id?: string" in TODO_SERVICE
