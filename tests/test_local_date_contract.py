from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_SERVICE = (ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts").read_text(encoding="utf-8")
API = (ROOT / "time-helper" / "desk" / "src" / "api" / "index.ts").read_text(encoding="utf-8")


def test_core_date_helpers_use_local_calendar_components():
    assert "date.getFullYear()" in DATA_SERVICE
    assert "date.getMonth() + 1" in DATA_SERVICE
    assert "date.getDate()" in DATA_SERVICE
    assert "now.toISOString().split('T')[0]" not in DATA_SERVICE
    assert "export function parseLocalDate" in DATA_SERVICE
    assert "new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))" in DATA_SERVICE


def test_public_date_api_reuses_local_date_helpers():
    assert "formatDate" in API
    assert "return addDays(dateStr, days)" in API
    assert "parseLocalDate(startDate)" in API
    assert "parseLocalDate(endDate)" in API
    assert "parseLocalDate(weekStart)" in API
    assert "new Date(startDate)" not in API
    assert "new Date(endDate)" not in API
    assert "current.toISOString().split('T')[0]" not in API
