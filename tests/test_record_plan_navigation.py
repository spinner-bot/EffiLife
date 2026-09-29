from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_time_record_can_navigate_back_to_linked_plan_task():
    assert "function openLinkedPlan(todoId: string)" in VIEW
    assert "path: '/plans'" in VIEW
    assert "plan: todo.related_plan_id" in VIEW
    assert "...(todo.related_plan_task_id ? { task: todo.related_plan_task_id } : {})" in VIEW
    assert 'class="record-plan-link"' in VIEW
    assert "todoById.get(record.todo_id)?.related_plan_id" in VIEW


def test_record_plan_navigation_has_bilingual_copy():
    assert I18N.count("'records.linkedPlan':") == 2
    assert I18N.count("'records.openPlan':") == 2

