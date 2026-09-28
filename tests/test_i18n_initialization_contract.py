from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_i18n_initialization_is_storage_safe_and_browser_aware():
    assert "typeof localStorage === 'undefined'" in SOURCE
    assert "navigator.languages" in SOURCE
    assert "navigator.language" in SOURCE
    assert "try {" in SOURCE and "localStorage.setItem(STORAGE_KEY" in SOURCE


def test_i18n_exposes_supported_locale_registry_and_document_language():
    assert "export const SUPPORTED_LOCALES" in SOURCE
    assert "document.documentElement.lang = locale" in SOURCE
    assert "localeOptions: [...SUPPORTED_LOCALES]" in SOURCE
