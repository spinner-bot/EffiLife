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
