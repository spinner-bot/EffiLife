from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_version_page_structural_labels_use_i18n():
    assert "t('settings.version.latestChanges')" in SETTINGS
    assert "t('settings.version.history')" in SETTINGS


def test_version_page_structural_labels_exist_in_both_locales():
    assert I18N.count("'settings.version.latestChanges'") == 2
    assert I18N.count("'settings.version.history'") == 2


def test_version_history_has_parallel_english_notes_without_dropping_chinese_history():
    version = (ROOT / "time-helper" / "desk" / "src" / "version.ts").read_text(encoding="utf-8")
    assert "const VERSION_HISTORY_EN: Record<string, string[]>" in version
    assert "getVersionChanges" in version
    assert "getVersionChanges(release, locale)" in SETTINGS
    assert "'1.5.0': [" in version
    assert "'1.0.0': [" in version
