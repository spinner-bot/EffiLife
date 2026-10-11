from pathlib import Path

import launcher.start as launcher


def test_startup_failure_hint_points_to_both_diagnostics_modes(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "launcher_log_path", lambda: tmp_path / "launcher.log")

    launcher.print_startup_failure_hint()

    output = capsys.readouterr().out
    assert "--doctor" in output
    assert "--diagnose" in output
    assert str(tmp_path / "launcher.log") in output


def test_launcher_reuse_message_is_readable_for_cjk_console_users():
    source = (Path(launcher.BASE_DIR) / "launcher" / "start.py").read_text(encoding="utf-8")

    assert "使用已运行的主服务" in source
    assert "浣跨敤宸茶繍琛岀殑涓绘湇鍔?" not in source


def test_port_conflict_prints_actionable_hint(monkeypatch, capsys):
    companion = object()
    monkeypatch.setattr(launcher, "start_companions", lambda _module, _env: [companion])
    monkeypatch.setattr(launcher, "service_is_ready", lambda _url: False)
    monkeypatch.setattr(launcher, "local_port_is_occupied", lambda _url: True)
    terminated = []
    monkeypatch.setattr(launcher, "terminate_process", lambda process: terminated.append(process))

    result = launcher.run_module(
        "test",
        {"test": {"name": "test", "available": True, "cmd": ["test"], "cwd": Path.cwd(), "url": "http://127.0.0.1:1420", "setup": None}},
    )

    assert result == 1
    assert terminated == [companion]
    assert "--doctor" in capsys.readouterr().out


def test_doctor_separates_development_readiness_from_distribution_readiness(capsys):
    report = {
        "version": "1.7.0",
        "launch_mode": "development",
        "python": "python",
        "node": "node",
        "npm": "npm",
        "installer_artifacts": [{"exists": True, "non_empty": True, "version_matches": False, "artifact_version": "1.0.11", "path": "old.exe"}],
        "modules": {"1": {"runtime_state": "stopped", "available": True, "url": "http://127.0.0.1:1420"}},
        "companions": {},
        "issues": [],
        "hints": [],
    }

    assert launcher.print_doctor_report(report) is True
    output = capsys.readouterr().out
    assert "Distribution status: not ready" in output
    assert "Launch status: READY" in output
    assert "Result: READY (development launch; distribution status shown above)" in output


def test_doctor_machine_report_separates_launch_and_distribution_ready():
    source = (Path(__file__).parents[1] / "launcher" / "start.py").read_text(encoding="utf-8")

    assert '"launch_ready": not issues' in source
    assert '"distribution_ready": bool(usable_installers)' in source


def test_release_signing_status_detects_android_and_windows_prerequisites(monkeypatch, tmp_path):
    sdk = tmp_path / "android-sdk"
    build_tools = sdk / "build-tools" / "35.0.0"
    build_tools.mkdir(parents=True)
    (build_tools / "apksigner.bat").write_text("", encoding="utf-8")
    (build_tools / "zipalign.exe").write_text("", encoding="utf-8")
    profile = tmp_path / "profile"
    (profile / ".android").mkdir(parents=True)
    (profile / ".android" / "debug.keystore").write_bytes(b"test")
    release_keystore = tmp_path / "release.keystore"
    release_keystore.write_bytes(b"release")
    certificate = tmp_path / "release.pfx"
    certificate.write_bytes(b"certificate")
    monkeypatch.setattr(launcher, "android_sdk_dir", lambda: sdk)
    monkeypatch.setenv("USERPROFILE", str(profile))
    monkeypatch.setenv("EFFILIFE_ANDROID_KEYSTORE", str(release_keystore))
    monkeypatch.setenv("EFFILIFE_WINDOWS_SIGNING_CERT", str(certificate))
    monkeypatch.setattr(launcher.shutil, "which", lambda name: "C:/Windows Kits/signtool.exe" if name == "signtool.exe" else None)

    status = launcher.release_signing_status()

    assert status["android"]["ready"] is True
    assert status["android"]["formal_ready"] is True
    assert status["android"]["apksigner"].endswith("apksigner.bat")
    assert status["android"]["zipalign"].endswith("zipalign.exe")
    assert status["windows"]["signtool"] == "C:/Windows Kits/signtool.exe"
    assert status["windows"]["formal_ready"] is True


def test_release_signing_status_reports_unsigned_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr(launcher, "android_sdk_dir", lambda: tmp_path / "missing-sdk")
    monkeypatch.setattr(launcher, "windows_signtool_candidates", lambda: [])
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)

    status = launcher.release_signing_status()

    assert status["android"]["ready"] is False
    assert status["windows"]["ready"] is False


def test_signing_tools_without_release_credentials_are_not_formal_ready(monkeypatch, tmp_path):
    sdk = tmp_path / "android-sdk"
    build_tools = sdk / "build-tools" / "35.0.0"
    build_tools.mkdir(parents=True)
    (build_tools / "apksigner.bat").write_text("", encoding="utf-8")
    (build_tools / "zipalign.exe").write_text("", encoding="utf-8")
    monkeypatch.setattr(launcher, "android_sdk_dir", lambda: sdk)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(launcher, "windows_signtool_candidates", lambda: [tmp_path / "signtool.exe"])
    (tmp_path / "signtool.exe").write_bytes(b"tool")
    monkeypatch.delenv("EFFILIFE_ANDROID_KEYSTORE", raising=False)
    monkeypatch.delenv("EFFILIFE_WINDOWS_SIGNING_CERT", raising=False)
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)

    status = launcher.release_signing_status()

    assert status["android"]["formal_ready"] is False
    assert status["windows"]["ready"] is True
    assert status["windows"]["formal_ready"] is False


def test_windows_signtool_can_be_found_in_the_windows_sdk(monkeypatch, tmp_path):
    signtool = tmp_path / "signtool.exe"
    signtool.write_bytes(b"tool")
    monkeypatch.setattr(launcher.shutil, "which", lambda _name: None)
    monkeypatch.setattr(launcher, "windows_signtool_candidates", lambda: [signtool])

    assert launcher.find_windows_signtool() == str(signtool)


def test_doctor_exposes_native_toolchain_readiness(capsys):
    report = {
        "version": "1.7.0",
        "launch_mode": "development",
        "python": "python",
        "node": "node",
        "npm": "npm",
        "rust_toolchain": {"cargo": None, "rustc": None, "available": False},
        "installer_artifacts": [],
        "modules": {},
        "companions": {},
        "issues": [],
        "hints": [],
    }

    assert launcher.print_doctor_report(report) is True
    output = capsys.readouterr().out
    assert "cargo: missing" in output
    assert "rustc: missing" in output
    assert "Native build: not ready" in output
