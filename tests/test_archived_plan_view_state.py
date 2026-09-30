from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_archive_deeplink_clears_stale_active_plan_selection():
    assert "if (route.query.archive)" in VIEW
    assert "selectedPlan.value = null" in VIEW
    assert "view.value = 'events'" in VIEW
    assert "searchTargetTaskId.value = null" in VIEW

