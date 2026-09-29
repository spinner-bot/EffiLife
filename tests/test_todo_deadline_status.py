from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_center_exposes_explicit_deadline_states():
    source = VIEW.read_text(encoding="utf-8")

    assert "type DeadlineState = 'overdue' | 'today' | 'upcoming'" in source
    assert "function getDeadlineState(deadline?: string)" in source
    assert "function deadlineStateLabel(deadline?: string)" in source
    assert ':class="getDeadlineState(todo.deadline)"' in source
    assert "tasks.deadlineOverdue" in source
    assert "tasks.deadlineToday" in source
    assert "tasks.deadlineUpcoming" in source


def test_deadline_states_are_bilingual():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.deadlineOverdue", "tasks.deadlineToday", "tasks.deadlineUpcoming"):
        assert source.count(f"'{key}'") == 2
