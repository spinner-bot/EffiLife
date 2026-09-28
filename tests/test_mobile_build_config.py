from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk"


def test_mobile_tauri_config_does_not_inherit_desktop_sidecar_build():
    config = json.loads((DESK / "src-tauri" / "tauri.mobile.conf.json").read_text(encoding="utf-8"))
    assert config["build"]["beforeBuildCommand"] == "npm run build"
    assert "sidecar" not in config["build"]["beforeBuildCommand"]
    assert config["bundle"]["externalBin"] == []


def test_desktop_tauri_config_retains_sidecar_contract():
    config = json.loads((DESK / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    assert "build:sidecar" in config["build"]["beforeBuildCommand"]
    assert config["bundle"]["externalBin"] == ["binaries/efflife-plan-helper"]
