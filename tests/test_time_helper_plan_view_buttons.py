import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue"


def test_plan_view_click_buttons_have_explicit_non_submit_types():
    source = VIEW.read_text(encoding="utf-8")
    buttons = re.findall(r"<button\b[\s\S]*?>", source)
    clickable_buttons = [button for button in buttons if "@click" in button]

    assert clickable_buttons
    assert all('type="button"' in button for button in clickable_buttons)
