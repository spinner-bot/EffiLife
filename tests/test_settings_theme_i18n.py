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
    "previewStatus",
)


def test_theme_editor_uses_translation_keys():
    source = SETTINGS.read_text(encoding="utf-8")
    for key in THEME_KEYS:
        assert f"t('settings.theme.{key}')" in source


def test_theme_editor_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in THEME_KEYS:
        assert source.count(f"'settings.theme.{key}'") == 2


def test_settings_subviews_use_localized_back_action():
    source = SETTINGS.read_text(encoding="utf-8")
    assert ">返回</button>" not in source
    assert source.count("t('settings.back')") >= 6


def test_locale_catalogs_have_the_same_translation_keys():
    source = I18N.read_text(encoding="utf-8")
    import re
    pattern = re.compile(r"^\s*'([^']+)':", re.MULTILINE)
    zh_match = re.search(r"'zh-CN':\s*\{(?P<body>.*?)\n  \},\n  'en-US':", source, re.S)
    en_match = re.search(r"'en-US':\s*\{(?P<body>.*?)\n  \},\n}\n\nfunction readLocale", source, re.S)
    assert zh_match and en_match
    zh_keys = set(pattern.findall(zh_match.group('body')))
    en_keys = set(pattern.findall(en_match.group('body')))
    assert zh_keys == en_keys
