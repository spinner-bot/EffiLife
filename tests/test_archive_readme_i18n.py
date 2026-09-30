from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_exported_archive_readme_uses_the_current_locale_catalog():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "translate('settings.archive.readme.title')" in source
    assert "toLocaleString(currentLocale.value)" in source
    assert "浪兮效率时钟存档文件" not in source


def test_archive_readme_catalog_has_both_supported_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "settings.archive.readme.title",
        "settings.archive.readme.protocol",
        "settings.archive.readme.version",
        "settings.archive.readme.exportedAt",
        "settings.archive.readme.includes",
        "settings.archive.readme.appData",
        "settings.archive.readme.planHelper",
        "settings.archive.readme.audioEvents",
        "settings.archive.readme.checkin",
        "settings.archive.readme.records",
        "settings.archive.readme.importMethod",
    ):
        assert source.count(f"'{key}'") == 2, key
