import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_build_environment.py"
SPEC = importlib.util.spec_from_file_location("effilife_build_environment", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_build_environment_reports_missing_required_tools(monkeypatch):
    monkeypatch.setattr(MODULE, "executable_path", lambda name: None if name in {"cargo", "rustc"} else f"/bin/{name}")
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)

    report = MODULE.build_report("desktop")

    assert report["ready"] is False
    assert report["missing"] == ["cargo", "rustc"]


def test_android_report_requires_sdk_root_in_addition_to_tool_binaries(monkeypatch):
    monkeypatch.setattr(MODULE, "executable_path", lambda name: f"/bin/{name}")
    monkeypatch.delenv("ANDROID_HOME", raising=False)
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)

    report = MODULE.build_report("android")

    assert report["ready"] is False
    assert "ANDROID_HOME or ANDROID_SDK_ROOT" in report["missing"]
