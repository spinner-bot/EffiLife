import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK_SRC = ROOT / "time-helper" / "desk" / "src"


def test_all_view_click_buttons_declare_non_submit_type():
    checked = 0
    files = list((DESK_SRC / "views").glob("*.vue")) + list((DESK_SRC / "components").glob("*.vue")) + [DESK_SRC / "App.vue"]
    for view in files:
        source = view.read_text(encoding="utf-8")
        buttons = re.findall(r"<button\b[\s\S]*?>", source)
        clickable_buttons = [button for button in buttons if "@click" in button]
        checked += len(clickable_buttons)
        assert all('type="button"' in button for button in clickable_buttons), view.name

    assert checked > 0
