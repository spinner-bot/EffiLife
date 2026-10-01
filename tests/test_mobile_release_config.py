from __future__ import annotations

import json
from pathlib import Path

from scripts.check_mobile_release_config import validate


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_release_config_isolated_from_desktop_sidecar():
    assert validate(ROOT) == []


def test_mobile_release_config_matches_repository_version_and_identity():
    mobile = json.loads((ROOT / "time-helper/desk/src-tauri/tauri.mobile.conf.json").read_text(encoding="utf-8"))
    desktop = json.loads((ROOT / "time-helper/desk/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    version = (ROOT / "time-helper/VERSION").read_text(encoding="utf-8").strip()
    assert mobile["version"] == version
    assert mobile["productName"] == desktop["productName"]
    assert mobile["identifier"] == desktop["identifier"]


def test_mobile_release_config_rejects_sidecar_regression(tmp_path):
    source = ROOT / "time-helper" / "desk" / "src-tauri"
    destination = tmp_path / "time-helper" / "desk" / "src-tauri"
    destination.mkdir(parents=True)
    (tmp_path / "time-helper").mkdir(exist_ok=True)
    (tmp_path / "time-helper" / "VERSION").write_text(
        (ROOT / "time-helper" / "VERSION").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name in ("tauri.conf.json", "tauri.mobile.conf.json"):
        (destination / name).write_text((source / name).read_text(encoding="utf-8"), encoding="utf-8")
    mobile_path = destination / "tauri.mobile.conf.json"
    mobile = json.loads(mobile_path.read_text(encoding="utf-8"))
    mobile["build"]["beforeBuildCommand"] = "npm run build:sidecar && npm run build"
    mobile_path.write_text(json.dumps(mobile), encoding="utf-8")
    errors = validate(tmp_path)
    assert any("sidecar" in error for error in errors)
