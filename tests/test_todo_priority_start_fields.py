from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_forms_expose_priority_rank_and_start_time():
    source = TASKS.read_text(encoding="utf-8")
    assert "start_time: fromDateTimeLocal(startTime.value)" in source
    assert "start_time: fromDateTimeLocal(editingStartTime.value)" in source
    assert "id=\"new-task-start-time\"" in source
    assert "id=\"new-task-priority-rank\"" in source
    assert "edit-start-time-${todo.id}" in source
    assert "edit-priority-rank-${todo.id}" in source


def test_task_start_time_and_priority_labels_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.startTime", "tasks.priorityRank"):
        assert source.count(f"'{key}'") == 2
