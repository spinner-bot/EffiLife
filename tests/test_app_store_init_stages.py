from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")


def test_app_store_initialization_reports_bounded_stage_failures():
    assert "async function waitForInitStage<T>" in STORE
    assert "Workspace initialization stalled at ${name}" in STORE
    for stage in ("data migration", "configuration", "plans", "schedule rules", "records", "today workspace"):
        assert f"waitForInitStage('{stage}'" in STORE
