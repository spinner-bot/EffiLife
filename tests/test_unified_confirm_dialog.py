from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "confirmService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_unified_shell_mounts_the_themed_confirm_host():
    source = APP.read_text(encoding="utf-8")
    assert "import ConfirmHost from './components/ConfirmHost.vue'" in source
    assert "<ConfirmHost />" in source


def test_confirm_service_resolves_the_user_decision():
    source = SERVICE.read_text(encoding="utf-8")
    assert "export function requestConfirm" in source
    assert "export function settleConfirm" in source
    assert "activeConfirm.value.resolve(false)" in source


def test_confirm_catalog_is_available_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("common.confirmTitle", "common.confirm", "common.cancel"):
        assert source.count(f"'{key}':") == 2
