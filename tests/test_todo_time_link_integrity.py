from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts").read_text(encoding="utf-8")


def test_tracking_time_deduplicates_related_record_ids():
    assert "const relatedTimeRecordIds = recordIds.length > 0" in SERVICE
    assert "[...new Set([...(current.related_time_record_ids || []), ...recordIds])]" in SERVICE
    assert "related_time_record_ids: relatedTimeRecordIds" in SERVICE
