from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_linked_plan_task_can_open_time_record_form():
    assert "async function openTaskRecord" in VIEW
    assert "await addTaskToTodos(task)" in VIEW
    assert "router.push({ path: '/records', query: { todo: todoId } })" in VIEW
    assert 'class="task-time"' in VIEW
    assert "@click=\"openTaskRecord(task)\"" in VIEW
    assert "plans.recordTodoTime" in VIEW


def test_plan_task_time_entry_has_bilingual_copy():
    assert I18N.count("'plans.recordTodoTime':") == 2
    assert "'plans.recordTodoTime': '记录用时'" in I18N
    assert "'plans.recordTodoTime': 'Record time'" in I18N
