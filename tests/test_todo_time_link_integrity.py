from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = (ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts").read_text(encoding="utf-8")


def test_tracking_time_deduplicates_related_record_ids():
    assert "const relatedTimeRecordIds = recordIds.length > 0" in SERVICE
    assert "const existingRecordIds = current.related_time_record_ids || []" in SERVICE
    assert "[...new Set([...existingRecordIds, ...recordIds])]" in SERVICE
    assert "related_time_record_ids: relatedTimeRecordIds" in SERVICE


def test_todo_normalization_deduplicates_imported_record_ids():
    assert "const relatedTimeRecordIds = Array.isArray(todo.related_time_record_ids)" in SERVICE
    assert "new Set(todo.related_time_record_ids.filter" in SERVICE


def test_tracking_same_record_batch_is_idempotent_for_time_spent():
    assert "const hasNewRecordId = recordIds.some((id) => !existingRecordIds.includes(id))" in SERVICE
    assert "const addedMinutes = recordIds.length > 0 && !hasNewRecordId ? 0 : minutes" in SERVICE
    assert "time_spent: (current.time_spent || 0) + addedMinutes" in SERVICE
