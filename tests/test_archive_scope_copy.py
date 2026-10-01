from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_archive_view_explains_the_three_unified_datasets_without_merging_domains():
    assert 'class="archive-scope theme-card"' in SETTINGS
    assert '<b>TH</b>{{ t(\'settings.archive.scopeTime\') }}' in SETTINGS
    assert '<b>PH</b>{{ t(\'settings.archive.scopePlans\') }}' in SETTINGS
    assert '<b>TD</b>{{ t(\'settings.archive.scopeTodos\') }}' in SETTINGS


def test_archive_scope_copy_is_localized_in_both_supported_locales():
    for key in (
        "settings.archive.scopeTitle",
        "settings.archive.scopeDescription",
        "settings.archive.scopeTime",
        "settings.archive.scopePlans",
        "settings.archive.scopeTodos",
    ):
        assert I18N.count(f"'{key}':") == 2
