from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_time_records_preserve_archived_plan_file_context_for_duplicate_ids():
    assert "listPlanArchives" in VIEW
    assert "listPlanSummaries" in VIEW
    assert "const archivedPlanById = computed" in VIEW
    assert "...(archivedPlan ? { archive: archivedPlan.file } : { plan: todo.related_plan_id })" in VIEW
    assert "!activePlanIds.value.has(String(archive.plan_id))" in VIEW

