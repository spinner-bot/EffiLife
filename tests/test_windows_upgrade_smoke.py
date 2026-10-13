from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_windows_upgrade.py").read_text(encoding="utf-8")


def test_windows_upgrade_smoke_can_verify_user_data_preservation():
    assert '"--data-dir"' in SCRIPT
    assert "_prepare_data_probe" in SCRIPT
    assert "_verify_data_probe" in SCRIPT
    assert "upgrade-preservation-probe.json" in SCRIPT
    assert "byte-identical" in SCRIPT
    assert '"data_probe": data_report' in SCRIPT


def test_windows_upgrade_smoke_refuses_existing_data_directory():
    assert "Upgrade smoke data directory already exists" in SCRIPT
    assert "Refusing to use a filesystem root or broad data directory" in SCRIPT
