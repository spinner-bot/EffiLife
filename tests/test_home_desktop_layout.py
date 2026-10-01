from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"


def test_home_uses_wide_desktop_control_panel_layout():
    source = HOME.read_text(encoding="utf-8")
    desktop_block = source.split("@media (min-width: 900px)", 1)[1].split(".stats-header-row", 1)[0]
    assert ".main-content" in desktop_block
    assert "max-width: 1180px" in desktop_block
    assert ".workflow-summary," in desktop_block
    assert "grid-column: 2; width: 100%" in desktop_block
    assert ".overview-grid { grid-template-columns:" in desktop_block
    assert "grid-template-columns: minmax(220px, .58fr) minmax(0, 1.42fr)" in desktop_block
    assert "grid-row: 1 / span 4" in desktop_block
    assert ".today-todos-card" in desktop_block


def test_home_keeps_mobile_and_tablet_breakpoints_distinct_from_desktop():
    source = HOME.read_text(encoding="utf-8")
    assert "@media (max-width: 760px)" in source
    assert "@media (min-width: 761px) and (max-width: 899px)" in source
    assert "@media (min-width: 900px)" in source
