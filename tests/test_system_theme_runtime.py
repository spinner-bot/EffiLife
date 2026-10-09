from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_system_theme_listener_is_registered_only_for_system_theme():
    assert "function syncSystemThemeMediaQuery()" in SOURCE
    assert "const shouldListen = appStore.config.theme.type === 'system'" in SOURCE
    assert "if (!shouldListen)" in SOURCE
    assert "stopSystemThemeMediaQuery()" in SOURCE
    assert "syncSystemThemeMediaQuery()" in SOURCE


def test_system_theme_listener_supports_modern_and_legacy_media_query_apis():
    assert "systemThemeMediaQuery.addEventListener('change', refreshSystemTheme)" in SOURCE
    assert "systemThemeMediaQuery.addListener(refreshSystemTheme)" in SOURCE
    assert "systemThemeMediaQuery.removeEventListener('change', refreshSystemTheme)" in SOURCE
    assert "systemThemeMediaQuery.removeListener(refreshSystemTheme)" in SOURCE


def test_system_theme_listener_is_cleaned_up_on_unmount_and_type_change():
    assert "onBeforeUnmount(() =>" in SOURCE
    assert "stopSystemThemeMediaQuery()" in SOURCE
    assert "watch(() => appStore.config.theme.type" in SOURCE
