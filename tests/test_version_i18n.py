from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "time-helper" / "desk" / "src" / "version.ts").read_text(encoding="utf-8")


def test_build_info_uses_current_locale_for_development_timestamp():
    assert "import { currentLocale } from './i18n'" in VERSION
    assert "toLocaleString(currentLocale.value)" in VERSION
    assert "toLocaleString('zh-CN')" not in VERSION
