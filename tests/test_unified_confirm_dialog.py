from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "confirmService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
LEGACY_CONFIRM_VIEWS = (
    ROOT / "time-helper" / "desk" / "src" / "views" / "MotionSettingsView.vue",
    ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue",
    ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue",
)


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


def test_settings_uses_themed_confirmation_service():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "import { requestConfirm } from '@/services/confirmService'" in source
    assert "confirm(" not in source


def test_compatibility_management_views_use_themed_confirmation_service():
    for view in LEGACY_CONFIRM_VIEWS:
        source = view.read_text(encoding="utf-8")
        assert "requestConfirm" in source, view.name
        assert "confirm(" not in source, view.name
