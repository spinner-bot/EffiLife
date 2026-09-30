import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDE_SOURCE = ROOT / "time-helper" / "desk" / "src" / "guide" / "GuideManager.ts"
OVERLAY_SOURCE = ROOT / "time-helper" / "desk" / "src" / "guide" / "GuideOverlay.vue"
I18N_SOURCE = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_onboarding_targets_unified_navigation():
    source = GUIDE_SOURCE.read_text(encoding="utf-8")
    current_steps = source.split("MAIN_GUIDE.steps = [", 1)[1].split("\n]", 1)[0]

    for key in ("plans", "tasks", "settings"):
        assert f'[data-guide="{key}"]' in current_steps
    assert "global-nav-link:nth-child" not in current_steps
    assert ".pv-tab" not in current_steps
    assert ".nav-btn" not in current_steps
    assert "actionType: 'input'" not in current_steps
    assert "this.backupData()" not in source
    assert "this.restoreData()" not in source


def test_onboarding_copy_is_localized_in_both_catalogs():
    guide = GUIDE_SOURCE.read_text(encoding="utf-8")
    overlay = OVERLAY_SOURCE.read_text(encoding="utf-8")
    catalog = I18N_SOURCE.read_text(encoding="utf-8")
    keys = set(re.findall(r"(?:titleKey|descriptionKey): '([^']+)'", guide))
    keys.update(re.findall(r"t\('([^']+)'\)", overlay))

    for key in keys:
        assert re.search(rf"'{re.escape(key)}':", catalog), f"missing guide i18n key: {key}"


def test_current_help_copy_does_not_advertise_retired_calendar_view():
    settings = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")
    catalog = I18N_SOURCE.read_text(encoding="utf-8")
    assert "legacy-help" not in settings
    assert "legacy-recovery" not in settings
    assert "CalendarDays" not in settings
    assert '可以将所有数据保存为JSON文件' not in settings
    assert '<strong>日历视图</strong>' not in settings
    assert '使用时间记录、日历和打卡' not in catalog
    assert 'Use time records, the calendar and check-ins' not in catalog


def test_guide_source_does_not_retain_retired_calendar_steps():
    guide = GUIDE_SOURCE.read_text(encoding="utf-8")
    assert "calendar" not in guide.lower()
    assert "日历" not in guide
    assert "navigateTo: '/calendar'" not in guide
