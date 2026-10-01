from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = (ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts").read_text(encoding="utf-8")


def test_plan_gateway_bounds_unresponsive_service_requests():
    assert "const PLAN_HELPER_REQUEST_TIMEOUT_MS = 8000" in GATEWAY
    assert "const controller = new AbortController()" in GATEWAY
    assert "controller.abort()" in GATEWAY
    assert "signal: controller.signal" in GATEWAY


def test_plan_gateway_preserves_caller_cancellation_and_cleans_up_timeout():
    assert "const externalAbort = () => controller.abort(options.signal?.reason)" in GATEWAY
    assert "options.signal?.addEventListener('abort', externalAbort" in GATEWAY
    assert "window.clearTimeout(timeout)" in GATEWAY
    assert "options.signal?.removeEventListener('abort', externalAbort)" in GATEWAY
