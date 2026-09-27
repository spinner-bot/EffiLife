from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_theme_preset_buttons_use_translation_keys():
    source = SETTINGS.read_text(encoding="utf-8")
    for key in (
        "default", "dark", "light", "purple", "blue", "sunset", "forest",
        "green", "pink", "cyan", "rainbow",
    ):
        assert f"t('settings.theme.preset.{key}')" in source


def test_theme_preset_catalogs_have_matching_entries():
    source = I18N.read_text(encoding="utf-8")
    for key in ("default", "dark", "light", "purple", "blue", "sunset", "forest", "green", "pink", "cyan", "rainbow"):
        assert f"'settings.theme.preset.{key}':" in source
