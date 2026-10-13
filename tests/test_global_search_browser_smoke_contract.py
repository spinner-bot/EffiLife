from pathlib import Path


SCRIPT = (Path(__file__).parents[1] / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_browser_smoke_exposes_unified_search_flow():
    assert "global_search_flow_verified" in SCRIPT
    assert "--global-search-flow" in SCRIPT
    assert "#global-search-trigger" in SCRIPT
    assert "#global-search-input" in SCRIPT
    assert "Smoke global search todo" in SCRIPT
    assert "global search result did not open the TD deep link" in SCRIPT
    assert "mobile_search_flow_verified" in SCRIPT
    assert "--mobile-search-flow" in SCRIPT
    assert "Smoke mobile search todo" in SCRIPT
    assert "mobile global search result did not open the TD deep link" in SCRIPT
