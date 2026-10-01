import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "to-dos" / "ui" / "src"


def test_compatibility_todo_ui_click_buttons_declare_non_submit_type():
    checked = 0
    for view in list((UI / "components").glob("*.vue")) + list((UI / "views").glob("*.vue")):
        source = view.read_text(encoding="utf-8")
        buttons = re.findall(r"<button\b[\s\S]*?>", source)
        clickable_buttons = [button for button in buttons if "@click" in button]
        checked += len(clickable_buttons)
        assert all('type="button"' in button for button in clickable_buttons), view.name

    assert checked > 0
