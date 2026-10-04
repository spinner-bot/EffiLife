from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / "time-helper" / "desk" / "src" / "services" / "runtimeCapabilities.ts").read_text(encoding="utf-8")
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
PLANS = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_mobile_runtime_exposes_a_positive_local_snapshot_capability_check():
    assert "export function isMobilePlanRuntime(): boolean" in RUNTIME
    assert "return getPlanRuntime() === 'mobile-unavailable'" in RUNTIME
    assert "local snapshot gateway" in RUNTIME


def test_dashboard_and_plan_hub_use_the_shared_mobile_capability_check():
    assert "import { isMobilePlanRuntime }" in HOME
    assert "const mobilePlanRuntime = isMobilePlanRuntime()" in HOME
    assert "getPlanRuntime() === 'mobile-unavailable'" not in HOME
    assert "import { isMobilePlanRuntime }" in PLANS
    assert "const mobilePlanRuntime = isMobilePlanRuntime()" in PLANS
    assert "getPlanRuntime() === 'mobile-unavailable'" not in PLANS
