from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_plan_editor_uses_ui_only_draft_ids_without_persisting_them():
    assert "type DraftPlanItem = PlanItem & { draftId: string }" in VIEW
    assert "function createDraftPlanItem(item: Partial<PlanItem> = {})" in VIEW
    assert ":key=\"item.draftId\"" in VIEW
    assert "map(({ draftId: _draftId, ...item }) => item)" in VIEW
