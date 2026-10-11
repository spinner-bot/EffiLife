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


def test_android_signing_requires_release_credentials_without_touching_input(tmp_path, monkeypatch):
    from scripts.sign_android_artifact import sign_android_artifact

    input_apk = tmp_path / "app-arm64-release-unsigned.apk"
    output_apk = tmp_path / "app-arm64-release.apk"
    input_apk.write_bytes(b"unsigned")
    zipalign = tmp_path / "zipalign"
    apksigner = tmp_path / "apksigner"
    zipalign.write_bytes(b"tool")
    apksigner.write_bytes(b"tool")
    for name in (
        "EFFILIFE_ANDROID_KEYSTORE_BASE64",
        "EFFILIFE_ANDROID_KEYSTORE_PASSWORD",
        "EFFILIFE_ANDROID_KEY_ALIAS",
        "EFFILIFE_ANDROID_KEY_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValueError, match="Missing required signing environment variable"):
        sign_android_artifact(input_apk, output_apk, zipalign=zipalign, apksigner=apksigner)

    assert input_apk.read_bytes() == b"unsigned"


def test_android_signing_replaces_unsigned_input_after_verified_output(tmp_path, monkeypatch):
    import subprocess

    from scripts import sign_android_artifact as signing

    input_apk = tmp_path / "app-arm64-release-unsigned.apk"
    output_apk = tmp_path / "app-arm64-release.apk"
    input_apk.write_bytes(b"unsigned")
    zipalign = tmp_path / "zipalign"
    apksigner = tmp_path / "apksigner"
    zipalign.write_bytes(b"tool")
    apksigner.write_bytes(b"tool")
    monkeypatch.setenv("EFFILIFE_ANDROID_KEYSTORE_BASE64", "a2V5")
    monkeypatch.setenv("EFFILIFE_ANDROID_KEYSTORE_PASSWORD", "store-secret")
    monkeypatch.setenv("EFFILIFE_ANDROID_KEY_ALIAS", "effilife")
    monkeypatch.setenv("EFFILIFE_ANDROID_KEY_PASSWORD", "key-secret")

    def fake_run(command, *, check, env):
        assert check is True
        if command[1] == "-f":
            Path(command[-1]).write_bytes(b"aligned")
        elif command[1] == "sign":
            Path(command[command.index("--out") + 1]).write_bytes(b"signed")
        elif command[1] == "verify":
            assert Path(command[-1]).read_bytes() == b"signed"
        else:
            raise AssertionError(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(signing.subprocess, "run", fake_run)

    assert signing.sign_android_artifact(input_apk, output_apk, zipalign=zipalign, apksigner=apksigner) == output_apk
    assert output_apk.read_bytes() == b"signed"
    assert not input_apk.exists()
