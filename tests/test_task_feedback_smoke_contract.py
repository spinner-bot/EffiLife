from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_td_browser_smoke_requires_success_feedback_after_completion():
    completion = SCRIPT.split('task_item.locator("button.task-check").click', 1)[1].split(
        'page.locator("#tasks-tab-completed")', 1
    )[0]
    assert 'page.locator(".toast-success").wait_for(state="visible", timeout=3000)' in completion

