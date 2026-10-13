from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKIN = (ROOT / "time-helper" / "desk" / "src" / "views" / "CheckinView.vue").read_text(encoding="utf-8")


def test_checkin_desktop_workbench_uses_two_columns_and_full_width_heatmap():
    assert "@media (min-width: 900px)" in CHECKIN
    assert "grid-template-columns: minmax(0, 1.15fr) minmax(320px, .85fr)" in CHECKIN
    assert ".heatmap-section { grid-column: 1 / -1; grid-row: 3; }" in CHECKIN


def test_checkin_mobile_layout_keeps_default_single_column_flow():
    assert "display: grid;" not in CHECKIN.split("@media (min-width: 900px)", 1)[0]
