from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_todo_deadline_display_requests_two_digit_month_and_day():
    assert "function formatDeadline(deadline?: string): string" in TASKS
    date_block = TASKS.split("function formatDeadline", 1)[1].split("function getDeadlineState", 1)[0]
    assert "new Intl.DateTimeFormat(locale.value" in date_block
    assert "month: '2-digit'" in date_block
    assert "day: '2-digit'" in date_block
    assert "date.toLocaleDateString(locale.value)" not in date_block


def test_todo_deadline_uses_local_calendar_date_parser_for_display_and_state():
    assert "parseStoredDate" in TASKS
    assert "const date = parseStoredDate(deadline)" in TASKS

    home = (ROOT / "time-helper/desk/src/views/HomeView.vue").read_text(encoding="utf-8")
    assert "parseStoredDate(deadline).toLocaleDateString" in home
