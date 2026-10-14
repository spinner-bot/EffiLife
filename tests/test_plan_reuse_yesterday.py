from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
GATEWAY = (ROOT / "time-helper/desk/src/services/planGateway.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_unified_plan_workspace_exposes_yesterday_reuse_action():
    assert "copyYesterdayPlan" in VIEW
    assert "@click=\"copyYesterday\"" in VIEW
    assert "plans.copyYesterday" in VIEW
    assert "plans.copiedYesterday" in VIEW


def test_yesterday_reuse_preserves_plan_structure_and_resets_execution_state():
    assert "'/api/plans/copy-yesterday'" in GATEWAY
    assert "copied.log = []" in GATEWAY
    assert "delete task.finish" in GATEWAY
    assert "taskCount = (plan: RawPlan)" in GATEWAY


def test_yesterday_reuse_has_bilingual_copy():
    assert I18N.count("'plans.copyYesterday':") == 2
    assert I18N.count("'plans.noYesterdayPlan':") == 2
