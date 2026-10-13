from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_browser_smoke_exposes_mobile_ph_snapshot_flow():
    assert "mobile_ph_plan_flow_verified" in SCRIPT
    assert '"--mobile-ph-plan-flow"' in SCRIPT
    assert "mobile-user-agent PH local snapshot create and edit flow" in SCRIPT
    assert "Mobile smoke plan edited" in SCRIPT

