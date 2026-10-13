from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "verify_release_candidate.py").read_text(encoding="utf-8")


def test_release_candidate_script_keeps_platform_and_build_gates_explicit():
    assert '"scripts/check_release_config.py"' in SCRIPT
    assert '"scripts/check_mobile_release_config.py"' in SCRIPT
    assert '"scripts/build_frontend.py"' in SCRIPT
    assert '"-m", "pytest", "-q"' in SCRIPT


def test_release_candidate_script_does_not_start_services_or_sign_artifacts():
    assert "smoke_browser_workspace" not in SCRIPT
    assert "sign_android_artifact" not in SCRIPT
    assert "tauri build" not in SCRIPT
