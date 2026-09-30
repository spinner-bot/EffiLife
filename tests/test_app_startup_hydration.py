from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_business_shell_mounts_only_after_storage_hydration():
    source = APP.read_text(encoding="utf-8")
    assert "const runtimeReady = ref(false)" in source
    assert "await Promise.all([AudioManager.whenReady(), CheckinSystem.whenReady(), EventSystem.whenReady()])" in source
    assert '<template v-if="runtimeReady">' in source
    assert 'class="app-startup" role="status"' in source


def test_startup_state_is_localized_in_both_fallback_catalogs():
    source = I18N.read_text(encoding="utf-8")
    assert "'app.starting': '\\u6b63\\u5728\\u51c6\\u5907\\u5de5\\u4f5c\\u53f0\\u2026'" in source
    assert "'app.starting': 'Preparing workspace…'" in source


def test_startup_error_exposes_localized_diagnostic_detail():
    app = APP.read_text(encoding="utf-8")
    source = I18N.read_text(encoding="utf-8")
    assert "const startupErrorMessage = ref('')" in app
    assert "startupErrorMessage.value = error instanceof Error ? error.message : String(error)" in app
    assert "app.startupFailedDetail" in app
    assert source.count("'app.startupFailedDetail'") == 4


def test_checkin_refresh_has_a_recoverable_error_boundary():
    app = APP.read_text(encoding="utf-8")
    checkin_block = app.split("function onCheckinComplete()", 1)[1].split("function onCheckinClose", 1)[0]
    assert "void appStore.refreshTodayData().catch((error) =>" in checkin_block
    assert "Failed to refresh today data after check-in:" in checkin_block


def test_automatic_checkin_maintenance_has_a_recoverable_error_boundary():
    app = APP.read_text(encoding="utf-8")
    maintenance = app.split("// 自动补打卡检查", 1)[1].split("// result === 'no-record'", 1)[0]
    assert "try {" in maintenance
    assert "await CheckinSystem.autoCheckinIfMissed()" in maintenance
    assert "await CheckinSystem.getYesterdayCompletedRecords()" in maintenance
    assert "Failed to complete automatic check-in maintenance:" in maintenance
