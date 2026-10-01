from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_schedule_rule_cards_use_content_identity_with_index_fallback():
    assert "function scheduleRuleKey(rule: ScheduleRule, index: number)" in VIEW
    assert "return `${rule.rule_type}-${rule.value}-${rule.plan_name}-${index}`" in VIEW
    assert ':key="scheduleRuleKey(rule, index)"' in VIEW
