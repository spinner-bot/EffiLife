from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_plan_task_uses_its_own_progress_log_instead_of_todo_time_bridge():
    assert "async function openTaskRecord" not in VIEW
    assert "addTaskToTodos" not in VIEW
    assert 'class="task-time"' not in VIEW
    assert "@submit.prevent=\"saveLog\"" in VIEW


def test_plan_progress_entry_has_bilingual_copy():
    assert I18N.count("'plans.recordProgress':") == 2
