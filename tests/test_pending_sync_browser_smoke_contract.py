from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_pending_sync_browser_smoke_exercises_durable_queue_recovery():
    assert "--pending-sync-recovery-flow" in SCRIPT
    assert "pending_sync_recovery_verified" in SCRIPT
    assert "pending_plan_todo_sync" in SCRIPT
    assert "page.close()" in SCRIPT
    assert "SMOKE-PENDING-SYNC-TODO" in SCRIPT
