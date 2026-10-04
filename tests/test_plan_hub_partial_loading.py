from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_hub_keeps_active_plans_when_archive_listing_is_unavailable():
    assert "const [activeResult, archiveResult] = await Promise.allSettled([" in VIEW
    assert "plans.value = activeResult.value" in VIEW
    assert "archives.value = archiveResult.status === 'fulfilled' ? archiveResult.value : []" in VIEW
    assert "Archive storage is an optional surface" in VIEW


def test_plan_hub_only_reports_unavailability_when_active_plan_listing_fails():
    load_block = VIEW.split("async function loadPlans()", 1)[1].split("async function refreshFromWorkspace", 1)[0]
    assert "activeResult.status === 'fulfilled'" in load_block
    assert "errorMessage.value = activeResult.reason instanceof Error" in load_block
    assert "errorMessage.value = archiveResult.reason" not in load_block
