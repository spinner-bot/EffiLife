from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_windows_installer.py").read_text(encoding="utf-8")


def test_windows_installer_smoke_is_bounded_and_isolated():
    assert 'parser.add_argument("--installer"' in SCRIPT
    assert 'parser.add_argument("--target"' in SCRIPT
    assert "if resolved.exists():" in SCRIPT
    assert "Refusing to use a filesystem root" in SCRIPT
    assert '"/S"' in SCRIPT
    assert 'f"/D={target}"' in SCRIPT
    assert "_wait_removed(target, timeout)" in SCRIPT


def test_windows_installer_smoke_checks_desktop_sidecar_and_uninstaller():
    for name in ("efflife-desk.exe", "efflife-plan-helper.exe", "uninstall.exe"):
        assert name in SCRIPT
    assert "Installation is incomplete" in SCRIPT
    assert "Installation directory was not removed" in SCRIPT
