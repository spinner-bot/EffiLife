from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_time_record_only_navigates_to_its_todo():
    assert "function openLinkedPlan" not in VIEW
    assert 'class="record-plan-link"' not in VIEW
    assert "function openLinkedTodo(todoId: string)" in VIEW


def test_record_todo_navigation_has_bilingual_copy():
    assert I18N.count("'records.linkedTodo':") == 2
    assert I18N.count("'records.openTodo':") == 2
