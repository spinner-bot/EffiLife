from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


THEME_KEYS = (
    "colorConfig",
    "gradientConfig",
    "glassConfig",
    "neonConfig",
    "backgroundColor",
    "windowBackground",
    "buttonBackground",
    "buttonText",
    "startColor",
    "endColor",
    "gradientDirection",
    "right",
    "left",
    "down",
    "up",
    "bottomRight",
    "topLeft",
    "glassOpacity",
    "blurAmount",
    "neonColor",
    "accentColor",
    "glowIntensity",
    "presetLabel",
    "chooseColor",
)


def test_theme_editor_uses_translation_keys():
    source = SETTINGS.read_text(encoding="utf-8")
    for key in THEME_KEYS:
        assert f"t('settings.theme.{key}')" in source


def test_theme_editor_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in THEME_KEYS:
        assert source.count(f"'settings.theme.{key}'") == 2
