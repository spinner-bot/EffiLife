from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")
OVERLAY = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "guide" / "GuideOverlay.vue").read_text(
    encoding="utf-8"
)


def test_browser_smoke_exposes_real_onboarding_flow():
    assert "onboarding_flow_verified" in SCRIPT
    assert "--onboarding-flow" in SCRIPT
    assert "efflife_guide_completed" in SCRIPT
    assert '.guide-tooltip' in SCRIPT
    assert '[data-guide="plans"]' in SCRIPT


def test_onboarding_backdrop_does_not_swallow_highlighted_navigation_clicks():
    backdrop_start = OVERLAY.index(".guide-backdrop {")
    backdrop_block = OVERLAY[backdrop_start : OVERLAY.index("}", backdrop_start) + 1]
    assert "pointer-events: none" in backdrop_block
