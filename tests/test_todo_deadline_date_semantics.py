from pathlib import Path


SOURCE = Path("time-helper/desk/src/views/TaskCenterView.vue").read_text(encoding="utf-8")


def test_todo_deadlines_compare_calendar_days_before_clock_time():
    deadline_function = SOURCE[SOURCE.index("function getDeadlineState"):SOURCE.index("function deadlineStateLabel")]

    assert "if (deadlineDay === today) return 'today'" in deadline_function
    assert "new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()" in deadline_function
    assert "if (date.getTime() < now.getTime()) return 'overdue'" not in deadline_function
