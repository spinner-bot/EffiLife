from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_forms_keep_start_time_internal_while_rank_lives_on_the_task_row():
    source = TASKS.read_text(encoding="utf-8")
    assert "start_time: fromDateTimeLocal" not in source
    assert 'type="datetime-local"' not in source
    assert "adjustTodoRank(todo, 1)" in source
    assert "adjustTodoRank(todo, -1)" in source
    assert "task-rank-control" in source


def test_task_start_time_and_priority_labels_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.startTime", "tasks.priorityRank"):
        assert source.count(f"'{key}'") == 2
