from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_th_record_smoke_covers_edit_and_delete_after_reload():
    assert "th_record_mutation_flow_verified" in SCRIPT
    assert "th_record_link_flow_verified" in SCRIPT
    assert "Smoke linked TD" in SCRIPT
    assert "Smoke linked record" in SCRIPT
    assert 'button.record-todo-link' in SCRIPT
    assert "Smoke time record edited" in SCRIPT
    assert "button.pv-icon-btn.danger" in SCRIPT
    assert "TH time record was not durable after reload" in SCRIPT
