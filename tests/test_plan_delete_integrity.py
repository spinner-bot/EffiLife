from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_legacy_plan_delete_preserves_a_valid_workspace_reference():
    block = VIEW.split("async function deletePlan", 1)[1].split("// 日程规则", 1)[0]
    assert "remainingNames.length === 0" in block
    assert "legacyPlan.cannotDeleteLastPlan" in block
    assert "const fallbackPlan = remainingNames[0]" in block
    assert "rule.plan_name === name ? { ...rule, plan_name: fallbackPlan }" in block
    assert "await appStore.saveScheduleRules(nextRules)" in block
    assert "Object.entries(previousManualPlans).filter(([, planName]) => planName !== name)" in block
    assert "await appStore.refreshTodayData()" in block


def test_last_plan_delete_guard_is_localized():
    assert I18N.count("'legacyPlan.cannotDeleteLastPlan':") == 2


def test_plan_delete_rolls_back_all_reference_writes_when_a_followup_step_fails():
    block = VIEW.split("async function deletePlan", 1)[1].split("// 日程规则", 1)[0]
    assert "const previousPlans = JSON.parse(JSON.stringify(plans.value)) as Plans" in block
    assert "const previousRules = scheduleRules.value.map((rule) => ({ ...rule }))" in block
    assert "const previousManualPlans = await DataService.loadManualPlans()" in block
    assert "try { await appStore.savePlans(previousPlans) }" in block
    assert "try { await appStore.saveScheduleRules(previousRules) }" in block
    assert "try { await DataService.saveManualPlans(previousManualPlans) }" in block
