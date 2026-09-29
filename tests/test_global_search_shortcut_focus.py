from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_global_search_shortcut_does_not_steal_editing_focus():
    assert "function isEditableTarget(target: EventTarget | null): boolean" in APP
    assert "target.isContentEditable" in APP
    assert "['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)" in APP
    assert "if (isEditableTarget(event.target)) return" in APP
    assert "event.ctrlKey || event.metaKey" in APP
