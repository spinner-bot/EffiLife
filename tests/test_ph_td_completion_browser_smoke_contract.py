from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_ph_td_smoke_covers_completion_projection_back_to_plan():
    assert "ph_td_completion_sync_verified" in SCRIPT
    assert "button.task-plan-reference" in SCRIPT
    assert "Smoke plan task" in SCRIPT
    assert "article.event-task-row" in SCRIPT
    assert "TD completion did not project back to the linked PH task" in SCRIPT
