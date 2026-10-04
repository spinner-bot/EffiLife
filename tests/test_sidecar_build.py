import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_plan_helper_sidecar.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("efflife_sidecar_builder", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sidecar_output_uses_tauri_target_suffix():
    builder = load_builder()

    assert builder.output_path("x86_64-pc-windows-msvc").name == (
        "efflife-plan-helper-x86_64-pc-windows-msvc.exe"
    )
    assert builder.output_path("aarch64-apple-darwin").name == (
        "efflife-plan-helper-aarch64-apple-darwin"
    )


def test_sidecar_prefers_tauri_selected_target_environment(monkeypatch):
    builder = load_builder()
    monkeypatch.setenv("TAURI_TARGET_TRIPLE", "x86_64-pc-windows-msvc")
    monkeypatch.setenv("TAURI_ENV_TARGET_TRIPLE", "aarch64-apple-darwin")

    assert builder.target_triple(None) == "aarch64-apple-darwin"


def test_sidecar_builder_rejects_empty_runtime_artifacts(tmp_path):
    builder = load_builder()
    empty = tmp_path / "efflife-plan-helper"
    empty.write_bytes(b"")
    non_empty = tmp_path / "efflife-plan-helper-non-empty"
    non_empty.write_bytes(b"sidecar")

    assert builder.is_non_empty_file(empty) is False
    assert builder.is_non_empty_file(non_empty) is True


def test_sidecar_install_replaces_atomically(tmp_path):
    builder = load_builder()
    generated = tmp_path / "generated.exe"
    destination = tmp_path / "binaries" / "efflife-plan-helper.exe"
    generated.write_bytes(b"new sidecar")

    builder.install_sidecar(generated, destination)

    assert destination.read_bytes() == b"new sidecar"
    assert not list(destination.parent.glob("*.tmp"))


def test_sidecar_install_reports_locked_destination(monkeypatch, tmp_path):
    builder = load_builder()
    generated = tmp_path / "generated.exe"
    destination = tmp_path / "binaries" / "efflife-plan-helper.exe"
    generated.write_bytes(b"new sidecar")

    def locked_replace(_source, _target):
        raise PermissionError("locked")

    monkeypatch.setattr(builder.os, "replace", locked_replace)

    try:
        builder.install_sidecar(generated, destination)
    except RuntimeError as error:
        assert "close the running EffiLife or Plan Helper process" in str(error)
    else:
        raise AssertionError("locked sidecar destination should be actionable")


def test_tauri_release_declares_sidecar_and_build_hook():
    config = json.loads(
        (ROOT / "time-helper/desk/src-tauri/tauri.conf.json").read_text(encoding="utf-8")
    )
    package = json.loads(
        (ROOT / "time-helper/desk/package.json").read_text(encoding="utf-8")
    )

    assert config["bundle"]["externalBin"] == ["binaries/efflife-plan-helper"]
    assert "build:sidecar" in config["build"]["beforeBuildCommand"]
    assert "build:sidecar" in package["scripts"]


def test_release_sidecar_is_killed_when_tauri_exits():
    source = (ROOT / "time-helper/desk/src-tauri/src/lib.rs").read_text(encoding="utf-8")

    assert "PlanHelperSidecarState" in source
    assert "RunEvent::ExitRequested" in source
    assert "child.kill()" in source


def test_release_sidecar_must_pass_health_check_before_app_startup():
    source = (ROOT / "time-helper/desk/src-tauri/src/lib.rs").read_text(encoding="utf-8")
    server = (ROOT / "plan-helper/web/server.py").read_text(encoding="utf-8")

    assert "plan_helper_is_ready" in source
    assert 'GET /api/health HTTP/1.1' in source
    assert 'response.contains("plan-helper")' in source
    assert "fn plan_helper_port_is_occupied() -> bool" in source
    assert 'if plan_helper_port_is_occupied() {' in source
    assert 'plan-helper port 8765 is already occupied' in source
    assert 'path == "/api/health"' in server
    assert "plan-helper sidecar did not pass its health check" in source
