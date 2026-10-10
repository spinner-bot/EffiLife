from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = (ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts").read_text(encoding="utf-8")


def test_plan_log_date_is_optional_and_preserved_in_mobile_projection():
    assert "date?: string" in GATEWAY
    assert "date: typeof log.date === 'string' ? log.date : undefined" in GATEWAY
