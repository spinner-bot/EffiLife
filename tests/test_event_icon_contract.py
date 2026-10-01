from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_SYSTEM = (ROOT / "time-helper" / "desk" / "src" / "audio" / "EventSystem.ts").read_text(encoding="utf-8")
EVENT_POPUP = (ROOT / "time-helper" / "desk" / "src" / "audio" / "EventPopup.vue").read_text(encoding="utf-8")
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_new_event_payloads_use_semantic_icon_ids_instead_of_emoji():
    icon_assignments = EVENT_SYSTEM.split("let icon = ''", 1)[1].split("const event: AppEvent", 1)[0]
    assert "icon = 'trophy'" in icon_assignments
    assert "icon = 'alert-triangle'" in icon_assignments
    assert not any(marker in icon_assignments for marker in ("🔥", "🎉", "🏆", "⚠️", "📝", "🗑️", "🔄", "🎊", "💤", "📊", "🌅"))
    assert "icon: 'trophy'" in EVENT_SYSTEM


def test_event_surfaces_resolve_theme_aware_icon_components():
    assert "getNotificationIcon(event.type)" in EVENT_POPUP
    assert "getNotificationIcon(entry.type)" in HOME
