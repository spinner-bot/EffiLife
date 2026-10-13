from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_td_smoke_covers_edit_complete_and_delete():
    assert "td_task_mutation_flow_verified" in SCRIPT
    assert "Smoke quick todo edited" in SCRIPT
    assert "Smoke delete todo" in SCRIPT
    assert "button.task-edit" in SCRIPT
    assert "button.task-delete" in SCRIPT
