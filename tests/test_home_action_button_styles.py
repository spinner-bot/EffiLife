from pathlib import Path


HOME = (Path(__file__).resolve().parents[1] / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_home_todo_navigation_buttons_reset_browser_defaults():
    styles = HOME.split(".today-todos-link", 1)[1].split(".today-todo-capture", 1)[0]
    assert "border: 0" in styles
    assert "background: transparent" in styles
    assert "cursor: pointer" in styles
    assert "font: inherit" in styles
