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


def test_i18n_can_refresh_locale_written_by_another_workspace_window():
    assert "export function refreshLocaleFromStorage(): void" in SOURCE
    assert "const next = readLocale()" in SOURCE
    assert "if (next === currentLocale.value) return" in SOURCE


def test_manual_locale_changes_broadcast_a_workspace_settings_event():
    assert "import { notifyWorkspaceChanged } from '@/services/workspaceEvents'" in SOURCE
    assert "if (changed) notifyWorkspaceChanged('settings')" in SOURCE
