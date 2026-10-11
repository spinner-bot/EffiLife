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


def test_settings_subviews_are_deep_linkable_and_keep_a_safe_fallback():
    assert "useRoute" in SETTINGS
    assert "route.query.view" in SETTINGS
    assert "function parseSettingsView" in SETTINGS
    assert ": 'main'" in SETTINGS
    assert "router.replace({ query: queryView ? { view: queryView } : {} })" in SETTINGS


def test_settings_query_navigation_rebuilds_internal_back_stack():
    assert "viewHistory.value = nextView === 'main' ? ['main'] : ['main', nextView]" in SETTINGS
    assert "if (nextView === 'restore') void loadDataStatus()" in SETTINGS
