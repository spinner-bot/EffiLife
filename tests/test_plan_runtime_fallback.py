from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper/desk/src/services/dataService.ts").read_text(encoding="utf-8")


def test_day_plan_resolution_ignores_missing_references_and_empty_rules():
    block = SOURCE.split("async getDayPlan", 1)[1].split("async saveDayPlan", 1)[0]
    assert "const resolvePlan = (planName: string | undefined): DayPlanInfo | null" in block
    assert "const manualPlan = resolvePlan(planName)" in block
    assert "const matchedPlan = resolvePlan(rule.plan_name)" in block
    assert "rules[rules.length - 1]?.plan_name" in block
    assert "return resolvePlan(firstPlanName) || { name: '', type: '切分制' }" in block
