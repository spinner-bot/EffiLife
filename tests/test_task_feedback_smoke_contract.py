from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_td_browser_smoke_requires_success_feedback_after_completion():
    completion = SCRIPT.split('task_item.locator("button.task-check").click', 1)[1].split(
        'page.locator("#tasks-tab-completed")', 1
    )[0]
    assert 'page.locator(".toast-success").wait_for(state="visible", timeout=3000)' in completion


def test_home_td_browser_smoke_covers_inline_capture_and_completion_feedback():
    assert 'home_capture = page.locator("#home-quick-todo-input")' in SCRIPT
    assert 'home_todo.locator("button.today-todo-complete").click(timeout=5000)' in SCRIPT
    assert 'home_todo.wait_for(state="hidden", timeout=5000)' in SCRIPT
    assert "home_td_completion_feedback_verified" in SCRIPT


def test_mobile_td_browser_smoke_covers_inline_capture_and_completion_feedback():
    assert 'mobile_capture = mobile_page.locator("#home-quick-todo-input")' in SCRIPT
    assert 'mobile_todo.locator("button.today-todo-complete").click(timeout=5000)' in SCRIPT
    assert 'mobile_td_task_flow_verified' in SCRIPT

