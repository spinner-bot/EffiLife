from pathlib import Path


APP = Path("time-helper/desk/src/App.vue").read_text(encoding="utf-8")
GUIDE = Path("time-helper/desk/src/guide/GuideManager.ts").read_text(encoding="utf-8")


def test_desktop_and_mobile_navigation_expose_semantic_guide_targets():
    for key in ("plans", "tasks", "records", "settings"):
        assert APP.count(f'data-guide="{key}"') == 2


def test_active_guide_uses_semantic_targets_instead_of_navigation_order():
    for key in ("plans", "tasks", "records", "settings"):
        assert f'[data-guide="{key}"]' in GUIDE
    assert "global-nav-link:nth-child" not in GUIDE
