import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_build_scripts_have_explicit_init_and_configured_build_commands():
    package = json.loads((ROOT / "time-helper/desk/package.json").read_text(encoding="utf-8"))
    scripts = package["scripts"]

    assert scripts["mobile:android:init"] == "tauri android init"
    assert scripts["mobile:ios:init"] == "tauri ios init"
    for target in ("android", "ios"):
        assert scripts[f"mobile:{target}:build"].startswith(f"tauri {target} build")
        assert "--config src-tauri/tauri.mobile.conf.json" in scripts[f"mobile:{target}:build"]


def test_mobile_build_scripts_remain_separate_from_desktop_sidecar_build():
    package = json.loads((ROOT / "time-helper/desk/package.json").read_text(encoding="utf-8"))
    desktop = json.loads((ROOT / "time-helper/desk/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    scripts = package["scripts"]
    assert "build:sidecar" in desktop["build"]["beforeBuildCommand"]
    for name in ("mobile:android:build", "mobile:ios:build"):
        assert "build:sidecar" not in scripts[name]


def test_mobile_artifact_verifier_accepts_non_empty_android_apk_and_ios_bundle(tmp_path):
    from scripts.verify_mobile_artifacts import verify

    apk_root = tmp_path / "apk"
    apk_root.mkdir()
    apk = apk_root / "release.apk"
    apk.write_bytes(b"apk")
    assert verify(apk_root, "android") == [apk]

    ios_root = tmp_path / "ios"
    bundle = ios_root / "EffiLife.app" / "Contents"
    bundle.mkdir(parents=True)
    (bundle / "Info.plist").write_bytes(b"plist")
    assert verify(ios_root, "ios") == [ios_root / "EffiLife.app"]


def test_mobile_artifact_verifier_rejects_empty_or_missing_outputs(tmp_path):
    from scripts.verify_mobile_artifacts import verify

    root = tmp_path / "outputs"
    root.mkdir()
    (root / "empty.apk").write_bytes(b"")
    with pytest.raises(FileNotFoundError):
        verify(root, "android")
