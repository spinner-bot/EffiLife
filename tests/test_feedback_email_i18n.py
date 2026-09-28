from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_feedback_email_templates_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'settings.feedback.emailSubject'") == 2
    assert source.count("'settings.feedback.emailBody'") == 2
    assert "{version}" in source


def test_settings_feedback_uses_localized_current_version_templates():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "t('settings.feedback.emailSubject')" in source
    assert "t('settings.feedback.emailBody', { version: appVersion })" in source
    assert "0.1.0" not in source
