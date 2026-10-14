from scripts.smoke_windows_installer import INSTALLER_VERSION_PATTERN


def test_installer_smoke_accepts_current_and_historical_product_names():
    assert INSTALLER_VERSION_PATTERN.match("EffiLife_1.7.0_x64-setup.exe").group("version") == "1.7.0"
    assert INSTALLER_VERSION_PATTERN.match("浪兮效率时钟_1.0.11_x64-setup.exe").group("version") == "1.0.11"


def test_installer_smoke_rejects_unversioned_or_unknown_names():
    assert INSTALLER_VERSION_PATTERN.match("EffiLife_x64-setup.exe") is None
    assert INSTALLER_VERSION_PATTERN.match("OtherProduct_1.0.0_x64-setup.exe") is None
