from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_plan_rename_removes_old_key_and_migrates_references():
    block = VIEW.split("async function savePlanInternal", 1)[1].split("async function deletePlan", 1)[0]
    assert "const editingOriginalPlanName = ref('')" in VIEW
    assert "if (originalName && originalName !== name) delete newPlans[originalName]" in block
    assert "rule.plan_name === originalName ? { ...rule, plan_name: name }" in block
    assert "await appStore.saveScheduleRules(nextRules)" in block
    assert "planName === originalName ? name : planName" in block
    assert "await appStore.refreshTodayData()" in block


def test_plan_rename_rejects_colliding_names_with_localized_feedback():
    block = VIEW.split("async function savePlanInternal", 1)[1].split("async function deletePlan", 1)[0]
    assert "Object.prototype.hasOwnProperty.call(plans.value, name)" in block
    assert "legacyPlan.planNameExists" in block
    assert I18N.count("'legacyPlan.planNameExists':") == 2
