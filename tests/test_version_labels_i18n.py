from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_version_build_labels_exist_in_both_locales():
    assert I18N.count("'version.build.development'") == 2
    assert I18N.count("'version.build.release'") == 2
