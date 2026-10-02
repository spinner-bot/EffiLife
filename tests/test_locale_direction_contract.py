from pathlib import Path


I18N = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_locale_definitions_carry_text_direction_metadata():
    assert "direction: 'ltr' | 'rtl'" in I18N
    assert "direction: 'ltr'" in I18N


def test_document_language_and_direction_follow_the_active_locale():
    assert "document.documentElement.lang = locale" in I18N
    assert "document.documentElement.dir = definition?.direction || 'ltr'" in I18N
