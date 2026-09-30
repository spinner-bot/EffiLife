from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tauri-mobile-boundary.yml"


def test_mobile_boundary_workflow_runs_configuration_and_frontend_contracts():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "python scripts/check_mobile_release_config.py" in source
    assert "tests/test_mobile_build_scripts.py tests/test_mobile_release_config.py" in source
    assert "working-directory: time-helper/desk" in source
    assert "run: npm run build" in source


def test_mobile_boundary_workflow_does_not_claim_to_publish_installers():
    source = WORKFLOW.read_text(encoding="utf-8").lower()
    assert "upload-artifact" not in source
    assert "release create" not in source
