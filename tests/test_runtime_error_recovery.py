from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "time-helper" / "desk" / "src" / "main.ts"
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_vue_runtime_errors_are_reported_to_the_recoverable_shell():
    source = MAIN.read_text(encoding="utf-8")
    assert "app.config.errorHandler" in source
    assert "effilife:runtime-error" in source
    assert "window.addEventListener('unhandledrejection'" in source


def test_runtime_error_notice_has_reload_and_dismiss_actions():
    source = APP.read_text(encoding="utf-8")
    assert "window.addEventListener('effilife:runtime-error', onRuntimeError)" in source
    assert 'role="alert" aria-live="assertive"' in source
    assert "@click=\"retryStartup\"" in source
    assert "@click=\"dismissRuntimeError\"" in source
    assert "app-runtime-error-detail" in source


def test_runtime_error_notice_is_localized_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("app.runtimeErrorTitle", "app.runtimeErrorDescription", "app.dismissRuntimeError"):
        assert source.count(f"'{key}':") == 2
