from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_settings_navigation_does_not_duplicate_the_current_view_in_history():
    navigation = SETTINGS.split("async function navigateTo(view: ViewType)", 1)[1].split("// 返回上一级", 1)[0]
    assert "if (currentView.value === view) return" in navigation
    assert navigation.index("if (currentView.value === view) return") < navigation.index("viewHistory.value.push(view)")


def test_settings_navigation_still_confirms_dirty_theme_before_switching():
    navigation = SETTINGS.split("async function navigateTo(view: ViewType)", 1)[1].split("// 返回上一级", 1)[0]
    assert "currentView.value === 'theme' && themeDirty.value" in navigation
    assert "const canLeave = await confirmThemeExit()" in navigation
