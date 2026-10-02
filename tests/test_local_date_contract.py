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


def test_user_visible_date_modules_parse_calendar_dates_locally():
    checkin = (ROOT / "time-helper" / "desk" / "src" / "data" / "CheckinSystem.ts").read_text(encoding="utf-8")
    checkin_view = (ROOT / "time-helper" / "desk" / "src" / "views" / "CheckinView.vue").read_text(encoding="utf-8")
    heatmap = (ROOT / "time-helper" / "desk" / "src" / "components" / "ContributionHeatmap.vue").read_text(encoding="utf-8")
    assert "parseLocalDate(this.data.value.lastCheckinDate)" in checkin
    assert "Math.round((today.getTime() - lastDate.getTime())" in checkin
    assert "parseLocalDate(dateStr)" in checkin_view
    assert "parseLocalDate(firstDay.date)" in heatmap
    assert "parseLocalDate(cell.date)" in heatmap


def test_archive_filename_uses_local_business_date():
    archive = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    assert "getTodayDate, normalizeConfig" in archive
    assert "const dateStr = getTodayDate()" in archive
    assert "new Date().toISOString().split('T')[0]" not in archive


def test_schedule_and_emergency_backup_use_local_business_dates():
    assert "const date = parseLocalDate(targetDay)" in DATA_SERVICE
    assert "const targetDate = parseLocalDate(targetDay)" in DATA_SERVICE
    assert "const todayDate = parseLocalDate(today)" in DATA_SERVICE
    settings = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")
    assert "DataService, getTodayDate" in settings
    assert "efflife_emergency_${getTodayDate()}.json" in settings


def test_archive_readme_export_time_follows_current_locale():
    archive = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    assert "import { currentLocale, setLocale, translate } from '@/i18n'" in archive
    assert "toLocaleString(currentLocale.value)" in archive
    assert "toLocaleString('zh-CN')" not in archive
