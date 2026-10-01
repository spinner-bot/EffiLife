from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_theme_selection_explicitly_updates_preview_and_dirty_draft():
    assert "function selectTheme(type: ThemeType)" in SETTINGS
    selection = SETTINGS.split("function selectTheme", 1)[1].split("// 主题引擎", 1)[0]
    assert "themeType.value = type" in selection
    assert "previewTheme()" in selection
    assert '@click="selectTheme(theme.type)"' in SETTINGS
