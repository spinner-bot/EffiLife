from pathlib import Path


ROOT = Path(__file__).parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_home_exposes_unfinished_ph_tasks_without_merging_them_into_todos():
    assert "getPlanFull" in HOME
    assert "completePlanTask" in HOME
    assert "focusPlanTasks" in HOME
    assert "openFocusPlan" in HOME
    assert "home.completePlanTask" in HOME
    assert "home.planTaskCompleted" in HOME
    assert "TodoService.create" not in HOME[HOME.index("async function completeHomePlanTask"):HOME.index("type TodoDeadlineState")]


def test_home_focus_only_reads_a_bounded_number_of_plan_details():
    assert ".slice(0, 2)" in HOME[HOME.index("const focusCandidates"):HOME.index("const details")]
    start = HOME.index("focusPlanTasks.value =", HOME.index("const details"))
    end = HOME.index("eventPlanState.value", start)
    assert ".slice(0, 5)" in HOME[start:end]
