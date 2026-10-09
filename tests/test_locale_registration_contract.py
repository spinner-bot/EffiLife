from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_locale_registry_accepts_optional_bcp47_like_codes():
    assert "export type Locale = string" in SOURCE
    assert "export function registerLocale(" in SOURCE
    assert "LOCALE_DEFINITIONS.push({ ...definition, code, fallback })" in SOURCE
    assert "SUPPORTED_LOCALES.push(code)" in SOURCE
    assert "catalogs[code] = { ...catalog }" in SOURCE


def test_locale_registration_rejects_empty_and_duplicate_codes_without_overwriting():
    assert "if (!code || LOCALE_DEFINITIONS.some(({ code: existing }) => existing.toLowerCase() === code.toLowerCase())) return false" in SOURCE
    assert "navigationFallbacks[code] = { ...navigationCatalog }" in SOURCE


def test_locale_detection_uses_registered_exact_and_language_prefix_matches():
    assert "function resolveRegisteredLocale(candidate: string): Locale | undefined" in SOURCE
    assert "code.toLowerCase() === normalized" in SOURCE
    assert "code.toLowerCase().split('-')[0] === language" in SOURCE
    assert "const resolved = resolveRegisteredLocale(candidate)" in SOURCE


def test_dynamic_locale_translation_keeps_registered_fallback_chain():
    assert "catalogs[currentLocale.value]?.[key]" in SOURCE
    assert "navigationFallbacks[currentLocale.value]?.[key]" in SOURCE
    assert "const fallbackCatalog = catalogs[fallbackLocale] || {}" in SOURCE
    assert "const fallbackNavigationCatalog = navigationFallbacks[fallbackLocale] || {}" in SOURCE


def test_runtime_locale_selection_reuses_registered_exact_and_prefix_resolution():
    assert "const resolved = resolveRegisteredLocale(next) || 'zh-CN'" in SOURCE
