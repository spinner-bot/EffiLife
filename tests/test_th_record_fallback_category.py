from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_th_record_form_has_a_category_without_a_daily_plan():
    assert "planTags.length > 0 ? planTags : [t('legacyPlan.uncategorized')]" in PLAN_VIEW
    assert "'legacyPlan.uncategorized': '未分类'" in I18N
    assert "'legacyPlan.uncategorized': 'Uncategorized'" in I18N


def test_th_plan_categories_remain_authoritative_when_present():
    assert "plan?.items.map(item => item.name).filter(Boolean)" in PLAN_VIEW
