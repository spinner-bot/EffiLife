from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")
RECOVERY = (ROOT / "time-helper/desk/src/components/RecoveryPanel.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_settings_reset_and_restore_share_a_destructive_busy_gate():
    assert "const settingsDestructiveBusy = ref(false)" in SETTINGS
    assert "if (settingsDestructiveBusy.value) return" in SETTINGS
    assert "settingsDestructiveBusy.value = true" in SETTINGS
    assert "settingsDestructiveBusy.value = false" in SETTINGS
    assert "finally" in SETTINGS
    assert ':disabled="settingsDestructiveBusy"' in SETTINGS


def test_recovery_panel_disables_actions_while_restore_is_running():
    assert "busy?: boolean" in RECOVERY
    assert ':disabled="busy"' in RECOVERY


def test_reset_failure_is_localized_in_both_locales():
    assert I18N.count("'settings.reset.failed':") == 2
