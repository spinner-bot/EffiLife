from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK_SRC = ROOT / "time-helper" / "desk" / "src" / "services"


def test_offline_plan_reset_has_a_server_sync_tombstone():
    reset_source = (DESK_SRC / "planReset.ts").read_text(encoding="utf-8")
    gateway_source = (DESK_SRC / "planGateway.ts").read_text(encoding="utf-8")
    archive_source = (DESK_SRC / "ArchiveService.ts").read_text(encoding="utf-8")

    assert "PLAN_HELPER_RESET_PENDING_KEY" in reset_source
    assert "/api/data/import" in reset_source
    assert "replace: true" in reset_source
    assert "syncPendingPlanHelperReset()" in gateway_source
    assert "markPlanHelperResetPending()" in archive_source
    assert "clearPlanHelperResetPending()" in archive_source
