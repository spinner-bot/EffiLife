from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK_SRC = ROOT / "time-helper" / "desk" / "src"


def test_settings_reset_warning_uses_theme_aware_icon_component():
    source = (DESK_SRC / "views" / "SettingsView.vue").read_text(encoding="utf-8")

    assert "AlertTriangle" in source
    assert "class=\"reset-warning\"" in source
    assert "⚠️" not in source


def test_unified_core_views_do_not_render_emoji_as_icons():
    emoji_markers = ("📌", "📋", "✅", "❌", "⚠", "⭐", "🔔", "🎯", "🚀", "📅", "📝")
    paths = (
        DESK_SRC / "views" / "HomeView.vue",
        DESK_SRC / "views" / "PlansHubView.vue",
        DESK_SRC / "views" / "TaskCenterView.vue",
        DESK_SRC / "views" / "SettingsView.vue",
    )

    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert not any(marker in source for marker in emoji_markers), path.name
