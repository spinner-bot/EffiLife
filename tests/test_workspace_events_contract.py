from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts"


def test_workspace_listener_unsubscribe_is_idempotent():
    source = SOURCE.read_text(encoding="utf-8")
    assert "let active = true" in source
    assert "if (!active) return" in source
    assert "active = false" in source
    assert "subscriberCount = Math.max(0, subscriberCount - 1)" in source
