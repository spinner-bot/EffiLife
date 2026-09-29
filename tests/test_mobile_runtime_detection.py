from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "time-helper" / "desk" / "src" / "services" / "runtimeCapabilities.ts"


def test_mobile_runtime_detection_uses_modern_and_legacy_signals():
    source = RUNTIME.read_text(encoding="utf-8")
    assert "userAgentData" in source
    assert ".mobile === true" in source
    assert "navigator.userAgent" in source
    assert "navigator.platform === 'MacIntel'" in source
    assert "navigator.maxTouchPoints > 1" in source
