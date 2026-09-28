from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "time-helper" / "desk" / "src" / "version.ts").read_text(encoding="utf-8")


def test_build_info_uses_current_locale_for_development_timestamp():
    assert "import { currentLocale, translate } from './i18n'" in VERSION
    assert "toLocaleString(currentLocale.value)" in VERSION
    assert "toLocaleString('zh-CN')" not in VERSION


def test_build_info_formats_release_timestamp_as_a_localized_date():
    assert "const releaseDate = new Date(parseInt(timestamp) || Date.now())" in VERSION
    assert "releaseDate.toLocaleDateString(currentLocale.value)" in VERSION
    assert "translate('version.build.release')" in VERSION


def test_build_info_uses_catalog_labels_for_build_mode():
    assert "translate('version.build.development')" in VERSION
