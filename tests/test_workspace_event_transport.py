from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts"


def test_workspace_events_have_a_restricted_environment_transport_fallback():
    source = EVENTS.read_text(encoding="utf-8")
    assert "const WORKSPACE_STORAGE_KEY = 'effilife_workspace_event'" in source
    assert "if (!deliveredRemotely)" in source
    assert "window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(message))" in source
    assert "event.key !== WORKSPACE_STORAGE_KEY || !event.newValue" in source


def test_workspace_event_payload_is_unique_for_repeated_same_source_changes():
    source = EVENTS.read_text(encoding="utf-8")
    assert "id: `${Date.now()}-${Math.random().toString(36).slice(2)}`" in source
    assert "Storage events are edge-triggered" in source


def test_workspace_event_fallback_preserves_origin_filtering():
    source = EVENTS.read_text(encoding="utf-8")
    assert "message.origin !== WORKSPACE_ORIGIN && message.source" in source
    assert "listener(message.source, true)" in source
