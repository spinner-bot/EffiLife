from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk"


def test_settings_uses_non_blocking_feedback_for_operations():
    source = (DESK / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")

    assert "notifyToast" in source
    assert "alert(" not in source


def test_toast_host_has_accessible_themable_states():
    source = (DESK / "src" / "components" / "ToastHost.vue").read_text(encoding="utf-8")

    for marker in (":role=\"toast.tone === 'error' ? 'alert' : 'status'\"", "toast-success", "toast-error", "prefers-reduced-motion"):
        assert marker in source
