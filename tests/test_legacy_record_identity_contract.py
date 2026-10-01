from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_legacy_plan_view_uses_stable_record_identity_keys():
    assert "function recordKey(record: TimeRecord, index: number)" in VIEW
    assert "return record.id || `${record.date}-${record.start}-${record.end}-${record.tag}-${index}`" in VIEW
    assert ':key="recordKey(record, index)"' in VIEW
