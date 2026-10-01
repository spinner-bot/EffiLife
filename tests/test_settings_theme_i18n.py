from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
RECOVERY = ROOT / "time-helper" / "desk" / "src" / "components" / "RecoveryPanel.vue"
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


def test_backup_timestamps_follow_current_locale():
    source = SETTINGS.read_text(encoding="utf-8")
    recovery = RECOVERY.read_text(encoding="utf-8")
    assert "const { t, locale } = useI18n()" in source
    assert "toLocaleString(locale.value)" in source
    assert "toLocaleString(locale)" in recovery
    assert "toLocaleString('zh-CN')" not in source


def test_selectable_tech_theme_has_a_theme_engine_preset():
    settings = SETTINGS.read_text(encoding="utf-8")
    engine = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")
    assert "getAvailableThemes()" in settings
    assert "{ type: 'tech', name: '科技'" in engine
    assert "tech: () => ({" in engine


def test_every_rich_theme_selection_has_an_engine_preset():
    import re

    engine = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")
    registry = engine.split("export function getAvailableThemes(): ThemeDefinition[]", 1)[1]
    types = set(re.findall(r"\{ type: '([^']+)'", registry))
    basic_types = {"solid", "gradient", "glass", "neon"}
    preset_source = engine.split("const themePresets", 1)[1].split("// 辅助函数", 1)[0]
    preset_types = set(re.findall(r"^\s{2}([A-Za-z0-9_]+): \(\) =>", preset_source, re.MULTILINE))

    assert types - basic_types
    assert types - basic_types <= preset_types


def test_settings_uses_theme_engine_registry():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "getAvailableThemes" in source
    assert "type ThemeDefinition" in source
    assert "const availableThemes = getAvailableThemes()" in source
    assert "const availableThemes = [" not in source


def test_theme_registry_owns_localized_display_metadata():
    settings = SETTINGS.read_text(encoding="utf-8")
    engine = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")
    index = (ROOT / "time-helper" / "desk" / "src" / "theme" / "index.ts").read_text(encoding="utf-8")
    assert "export interface ThemeDefinition" in engine
    assert "nameKey: string" in engine
    assert "descriptionKey: string" in engine
    assert "categoryKey: string" in engine
    assert "getAvailableThemes(): ThemeDefinition[]" in engine
    assert "export type { ThemeDefinition, ThemeStyle }" in index
    assert "const themeMeta" not in settings
    assert "return theme.categoryKey" in settings
    assert "return t(theme.nameKey)" in settings
    assert "return t(theme.descriptionKey)" in settings


def test_theme_categories_are_derived_from_the_registry():
    settings = SETTINGS.read_text(encoding="utf-8")
    engine = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")
    assert "getAvailableThemeCategories" in engine
    assert "new Set(getAvailableThemes().map(theme => theme.categoryKey))" in engine
    assert "getAvailableThemeCategories" in settings
    assert "const availableThemeCategories = getAvailableThemeCategories()" in settings
    assert "v-for=\"category in availableThemeCategories\"" in settings
    assert "theme.category.basic" not in settings
    assert "theme.category.art" not in settings
    assert "theme.category.nature" not in settings
    assert "theme.category.tech" not in settings


def test_theme_registry_translation_keys_exist_in_every_locale():
    import re

    engine = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    registry = engine.split("export function getAvailableThemes(): ThemeDefinition[]", 1)[1]
    keys = set(re.findall(r"(?:nameKey|descriptionKey|categoryKey): '([^']+)'", registry))
    types = re.findall(r"\{ type: '([^']+)'", registry)
    assert keys
    assert len(types) == len(set(types))
    for key in sorted(keys):
        assert catalog.count(f"'{key}':") == 2, f"theme translation key is not present in both locales: {key}"


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


def test_theme_save_failure_message_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'settings.saveFailed'") == 2
