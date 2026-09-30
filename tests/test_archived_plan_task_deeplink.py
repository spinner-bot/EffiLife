from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_archived_task_search_target_is_rendered_without_mutating_the_archive():
    assert "type PlanTaskSummary," in VIEW
    assert "const archivedTaskTargetId = computed" in VIEW
    assert "function isArchivedTaskTarget" in VIEW
    assert "archivedPlanTarget.tasks?.length" in VIEW
    assert "isArchivedTaskTarget(task)" in VIEW
    assert "route.query.archive" in VIEW
