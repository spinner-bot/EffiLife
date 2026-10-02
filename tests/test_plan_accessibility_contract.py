from pathlib import Path


PLAN_VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_legacy_plan_icon_actions_have_explicit_accessible_names():
    assert 'openEditForm(index)\" :title=\"t(\'legacyPlan.edit\')\" :aria-label=\"t(\'legacyPlan.edit\')\"' in PLAN_VIEW
    assert 'deleteRecord(index)\" :title=\"t(\'legacyPlan.delete\')\" :aria-label=\"t(\'legacyPlan.delete\')\"' in PLAN_VIEW
    assert 'deletePlan(name as string)\" :title=\"t(\'legacyPlan.delete\')\" :aria-label=\"t(\'legacyPlan.delete\')\"' in PLAN_VIEW
    assert 'moveRuleUp(index)\" :title=\"t(\'legacyPlan.moveUp\')\" :aria-label=\"t(\'legacyPlan.moveUp\')\"' in PLAN_VIEW
    assert 'class=\"pv-modal-close\"' in PLAN_VIEW
    assert ':aria-label=\"t(\'common.cancel\')\"' in PLAN_VIEW
