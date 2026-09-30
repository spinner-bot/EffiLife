from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_time_workspace_action_cards_use_theme_tokens():
    for class_name in (
        "pv-action-icon-plan",
        "pv-action-icon-schedule",
        "pv-action-icon-temporary",
        "pv-action-icon-history",
    ):
        assert f"class=\"pv-action-icon {class_name}\"" in PLAN_VIEW
    assert "rgba(99,102,241" not in PLAN_VIEW
    assert "rgba(34,197,94" not in PLAN_VIEW
    assert "rgba(245,158,11" not in PLAN_VIEW
    assert "rgba(14,165,233" not in PLAN_VIEW
    assert "--icon-bg: var(--color-" in PLAN_VIEW
