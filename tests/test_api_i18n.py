from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API = (ROOT / "time-helper" / "desk" / "src" / "api" / "index.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_legacy_frontend_api_errors_use_the_shared_locale_catalog():
    assert "function apiFail<T>(key: string): ApiResponse<T>" in API
    assert "return fail(translate(`api.error.${key}`))" in API
    assert "return fail('" not in API


def test_frontend_api_error_catalog_is_bilingual():
    keys = [
        "loadConfig", "saveConfig", "updateConfig", "resetConfig",
        "loadPlans", "savePlans", "getPlan", "savePlan", "deletePlan",
        "getTodayPlan", "getDayPlan", "setDayPlan", "getScheduleRules",
        "saveScheduleRules", "loadRecords", "addRecord", "deleteRecord",
        "updateRecord", "getRecordRange", "getStats", "getStatsSummary",
        "getCheckinData", "checkin", "makeUpCheckin", "getCheckinRecords",
        "getCheckinStatus", "getCheckinRange", "resetCheckin",
        "updateEventSettings", "markRead", "markAllRead", "deleteInboxEntry",
        "clearInbox", "addWarningRule", "updateWarningRule",
        "deleteWarningRule", "triggerEvent", "getWeeklyReport",
        "getMonthlyTrend", "getSummary",
    ]
    for key in keys:
        assert I18N.count(f"'api.error.{key}'") == 2
