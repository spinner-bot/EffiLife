from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_windows_upgrade.py").read_text(encoding="utf-8")
INSTALL_SCRIPT = (ROOT / "scripts" / "smoke_windows_installer.py").read_text(encoding="utf-8")


def test_windows_upgrade_smoke_requires_two_installers_and_isolated_target():
    assert 'parser.add_argument("--previous-installer"' in SCRIPT
    assert 'parser.add_argument("--installer"' in SCRIPT
    assert 'parser.add_argument("--target"' in SCRIPT
    assert "_ensure_safe_target(target)" in SCRIPT
    assert '"/S"' in SCRIPT
    assert "f\"/D={target}\"" in SCRIPT


def test_windows_upgrade_smoke_verifies_current_files_and_cleanup():
    for name in ("efflife-desk.exe", "efflife-plan-helper.exe", "uninstall.exe"):
        assert name in INSTALL_SCRIPT
    assert "Upgrade installation is incomplete" in SCRIPT
    assert "Upgraded installation directory was not removed" in SCRIPT
    assert "INSTALLER_VERSION_PATTERN" in SCRIPT
    assert "Previous installer filename does not match a supported EffiLife NSIS convention" in SCRIPT
    assert "Previous installer must be a different EffiLife version" in SCRIPT


def test_windows_upgrade_smoke_can_verify_an_isolated_data_probe():
    assert '"--data-dir"' in SCRIPT
    assert "_prepare_data_probe" in SCRIPT
    assert "User data probe changed or disappeared" in SCRIPT
    assert "preserved" in SCRIPT
