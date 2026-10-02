from pathlib import Path


ARCHIVE = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")


def test_archive_import_applies_locale_through_the_shared_i18n_boundary():
    assert "import { currentLocale, setLocale, translate } from '@/i18n'" in ARCHIVE
    assert "if (data.locale === 'zh-CN' || data.locale === 'en-US')" in ARCHIVE
    assert "setLocale(data.locale)" in ARCHIVE
    assert "localStorage.setItem('effilife_locale', data.locale)" not in ARCHIVE
