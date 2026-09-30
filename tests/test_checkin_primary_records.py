from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKIN = ROOT / "time-helper" / "desk" / "src" / "data" / "CheckinSystem.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"


def test_checkin_completion_checks_primary_record_store():
    source = CHECKIN.read_text(encoding="utf-8")
    assert "async getCompletedRecordsForDate" in source
    assert "STORE_NAMES.RECORDS, dateStr" in source
    assert "async checkinForDate" in source
    assert "async autoCheckinIfMissed" in source


def test_app_awaits_primary_record_check_before_auto_checkin():
    source = APP.read_text(encoding="utf-8")
    assert "await CheckinSystem.autoCheckinIfMissed()" in source
    assert "await CheckinSystem.getYesterdayCompletedRecords()" in source


def test_checkin_fallback_plan_names_use_shared_i18n():
    source = CHECKIN.read_text(encoding="utf-8")
    catalog = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    assert "translate('settings.events.runtime.autoCheckinTitle')" in source
    assert "translate('settings.events.runtime.unknownPlan')" in source
    assert catalog.count("'settings.events.runtime.unknownPlan'") == 2
