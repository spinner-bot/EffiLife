from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
SWITCHER = (ROOT / "time-helper" / "desk" / "src" / "components" / "LocaleSwitcher.vue").read_text(encoding="utf-8")


def test_locale_registry_is_the_single_selection_source():
    assert "export interface LocaleDefinition" in I18N
    assert "export const LOCALE_DEFINITIONS" in I18N
    assert "LOCALE_DEFINITIONS.map(({ code }) => code)" in I18N
    assert "localeDefinitions" in I18N
    assert "v-for=\"option in localeDefinitions\"" in SWITCHER
    assert "option.labelKey" in SWITCHER


def test_locale_registry_keeps_current_languages_and_fallbacks():
    assert "{ code: 'zh-CN', labelKey: 'locale.zh-CN', fallback: 'zh-CN', direction: 'ltr' }" in I18N
    assert "{ code: 'en-US', labelKey: 'locale.en-US', fallback: 'zh-CN', direction: 'ltr' }" in I18N
    assert "const resolved = resolveRegisteredLocale(next) || 'zh-CN'" in I18N


def test_translation_uses_the_registered_locale_fallback():
    assert "const fallbackLocale = LOCALE_DEFINITIONS.find(({ code }) => code === currentLocale.value)?.fallback || 'zh-CN'" in I18N
    assert "catalogs[fallbackLocale][key]" in I18N
    assert "navigationFallbacks[fallbackLocale][key]" in I18N
    assert "catalogs['zh-CN'][key]" not in I18N
