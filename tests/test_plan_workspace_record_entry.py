from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
PLAN = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_primary_navigation_exposes_time_records_without_replacing_the_time_workspace():
    assert 'data-guide="records"' in APP
    assert 'to="/records"' in APP
    assert 'to="/time"' in APP


def test_plan_workspace_keeps_history_as_a_secondary_entry():
    assert "legacyPlan.historyRecords" in PLAN
    assert "legacyPlan.historyRecordsDescription" in PLAN
    assert "router.push('/records')" in PLAN


def test_plan_view_resolves_record_edits_by_stable_id():
    assert "const editingRecordId = ref<string | null>(null)" in PLAN
    assert "editingRecordId.value = record.id || null" in PLAN
    assert "const resolvedEditingIndex = isEditing.value && editingRecordId.value" in PLAN
    assert "records.value.findIndex((item) => item.id === editingRecordId.value)" in PLAN
    assert "appStore.updateRecord(resolvedEditingIndex, record)" in PLAN
    assert "legacyPlan.recordMissing" in PLAN


def test_plan_view_delete_resolves_current_record_by_stable_id():
    assert "const requestedRecord = records.value[index]" in PLAN
    assert "const resolvedIndex = requestedRecord?.id" in PLAN
    assert "await appStore.deleteRecord(resolvedIndex)" in PLAN
    assert "legacyPlan.recordMissing" in PLAN
