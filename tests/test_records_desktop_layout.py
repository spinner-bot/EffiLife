from pathlib import Path


VIEW = (Path(__file__).resolve().parents[1] / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_records_workspace_uses_desktop_width_without_changing_mobile_default():
    desktop = VIEW.split("@media (min-width: 1100px)", 1)[1].split("@keyframes", 1)[0]
    assert ".main-content { max-width: 1180px; }" in desktop
    assert ".records-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }" in desktop
    assert "@media (max-width: 680px)" in VIEW
