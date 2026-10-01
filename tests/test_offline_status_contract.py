from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_shell_tracks_browser_connectivity_for_offline_feedback():
    assert "const isOnline = ref(typeof navigator === 'undefined' ? true : navigator.onLine)" in APP
    assert "window.addEventListener('online', updateOnlineStatus)" in APP
    assert "window.addEventListener('offline', updateOnlineStatus)" in APP
    assert "window.removeEventListener('online', updateOnlineStatus)" in APP
    assert "window.removeEventListener('offline', updateOnlineStatus)" in APP
    assert "if (!wasOnline && isOnline.value) notifyWorkspaceChanged('network')" in APP
    assert "'network'" in (ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts").read_text(encoding="utf-8")


def test_shell_exposes_local_first_offline_status_in_both_locales():
    assert '<div v-if="!isOnline" class="offline-status" role="status" aria-live="polite">' in APP
    assert I18N.count("'app.offlineStatus'") == 2


def test_plan_center_accepts_network_recovery_events():
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "['plans', 'archive', 'network']" in plans
