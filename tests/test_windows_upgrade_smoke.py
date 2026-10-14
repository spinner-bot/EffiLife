from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_windows_upgrade.py").read_text(encoding="utf-8")
INSTALLER_SCRIPT = ROOT / "scripts" / "smoke_windows_installer.py"


def _installer_module():
    spec = importlib.util.spec_from_file_location("effilife_windows_installer", INSTALLER_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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


def test_installer_version_pattern_accepts_historical_chinese_brand():
    pattern = _installer_module().INSTALLER_VERSION_PATTERN
    match = pattern.match("浪兮效率时钟_1.0.11_x64-setup.exe")
    assert match is not None
    assert match.group("version") == "1.0.11"


def test_installer_version_pattern_accepts_historical_desk_release_suffix():
    pattern = _installer_module().INSTALLER_VERSION_PATTERN
    match = pattern.match("浪兮效率时钟_v1.0.11（desk_发布版）.exe")
    assert match is not None
    assert match.group("version") == "v1.0.11"
