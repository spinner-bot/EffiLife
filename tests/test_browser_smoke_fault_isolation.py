from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_browser_smoke_documents_fault_flow_isolation():
    assert "fault_flows = [" in SCRIPT
    assert "fault-injection browser smoke flows must run separately" in SCRIPT
    for flag in (
        "--inject-write-failure",
        "--startup-recovery-flow",
        "--archive-invalid-flow",
        "--archive-write-failure-flow",
    ):
        assert f'"{flag}"' in SCRIPT


def test_browser_smoke_rejects_multiple_fault_flows_without_starting_browser():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("smoke_browser_workspace", ROOT / "scripts" / "smoke_browser_workspace.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    with pytest.raises(ValueError, match="must run separately"):
        module.run_smoke(
            "http://127.0.0.1:1",
            startup_recovery_flow=True,
            archive_invalid_flow=True,
        )
