from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_primary_mobile_edit_surfaces_respect_bottom_safe_area():
    records = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
    plan_hub = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")

    assert "padding-bottom: max(var(--spacing-lg), env(safe-area-inset-bottom));" in records
    assert "padding-bottom: max(var(--spacing-lg), env(safe-area-inset-bottom));" in plans
    assert "padding-bottom: max(24px, env(safe-area-inset-bottom));" in plan_hub
