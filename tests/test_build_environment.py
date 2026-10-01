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


def test_android_report_exposes_missing_generated_tauri_project(monkeypatch, tmp_path):
    monkeypatch.setattr(MODULE, "executable_path", lambda name: f"/bin/{name}")
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path / "android-sdk"))
    monkeypatch.setattr(MODULE, "ROOT", tmp_path)

    report = MODULE.build_report("android")

    assert report["mobile_project"] == str(tmp_path / "time-helper/desk/src-tauri/gen/android")
    assert report["mobile_project_exists"] is False
    assert "Tauri android project (run tauri android init)" in report["missing"]


def test_android_report_is_ready_when_tools_sdk_and_generated_project_exist(monkeypatch, tmp_path):
    monkeypatch.setattr(MODULE, "executable_path", lambda name: f"/bin/{name}")
    sdk_root = tmp_path / "android-sdk"
    sdk_root.mkdir()
    monkeypatch.setenv("ANDROID_HOME", str(sdk_root))
    project = tmp_path / "time-helper/desk/src-tauri/gen/android"
    project.mkdir(parents=True)

    report = MODULE.build_report("android", tmp_path)

    assert report["ready"] is True
    assert report["mobile_project_exists"] is True
    assert report["missing"] == []


def test_android_report_rejects_a_nonexistent_sdk_root(monkeypatch, tmp_path):
    monkeypatch.setattr(MODULE, "executable_path", lambda name: f"/bin/{name}")
    monkeypatch.setenv("ANDROID_HOME", str(tmp_path / "missing-sdk"))

    report = MODULE.build_report("android")

    assert report["ready"] is False
    assert "Android SDK directory" in report["missing"]


def test_ios_report_uses_tauri_apple_project_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(MODULE, "executable_path", lambda _name: "/bin/tool")
    project = tmp_path / "time-helper/desk/src-tauri/gen/apple"
    project.mkdir(parents=True)

    report = MODULE.build_report("ios", tmp_path)

    assert report["mobile_project"] == str(project)
    assert report["mobile_project_exists"] is True
    assert report["missing"] == []


def test_node_tool_path_prefers_configured_custom_directory(monkeypatch, tmp_path):
    custom_dir = tmp_path / "node"
    custom_dir.mkdir()
    node_name = "node.exe" if MODULE.os.name == "nt" else "node"
    npm_name = "npm.cmd" if MODULE.os.name == "nt" else "npm"
    node_path = custom_dir / node_name
    npm_path = custom_dir / npm_name
    node_path.write_text("node", encoding="utf-8")
    npm_path.write_text("npm", encoding="utf-8")
    monkeypatch.setenv("EFFILIFE_NODE_DIR", str(custom_dir))
    monkeypatch.setattr(MODULE, "executable_path", lambda _name: "/system/tool")

    assert MODULE.node_tool_path("node") == str(node_path)
    assert MODULE.node_tool_path("npm") == str(npm_path)


def test_node_tool_path_falls_back_to_system_path(monkeypatch, tmp_path):
    monkeypatch.setenv("EFFILIFE_NODE_DIR", str(tmp_path / "missing"))
    monkeypatch.setattr(MODULE, "executable_path", lambda name: f"/system/{name}")

    assert MODULE.node_tool_path("node") == "/system/node"
    assert MODULE.node_tool_path("npm") == "/system/npm"
