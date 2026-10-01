from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper" / "desk" / "src" / "App.vue").read_text(encoding="utf-8")


def test_optional_startup_services_have_a_bounded_wait():
    assert "OPTIONAL_STARTUP_TIMEOUT_MS = 5000" in APP
    assert "async function waitForOptionalSubsystem" in APP
    assert "Promise.race([" in APP
    assert "clearTimeout(timeout)" in APP


def test_core_workspace_initialization_remains_after_optional_services():
    optional_block = APP.split("optionalStartup = Promise.all([", 1)[1].split("await appStore.init()", 1)[0]
    assert "waitForOptionalSubsystem('audio'" in optional_block
    assert "waitForOptionalSubsystem('check-in'" in optional_block
    assert "waitForOptionalSubsystem('events'" in optional_block
    assert "let optionalStartup: Promise<void> = Promise.resolve()" in APP
    assert "await optionalStartup" in APP
    assert "await appStore.init()" in APP
