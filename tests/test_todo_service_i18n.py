import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_todo_service_domain_errors_use_localized_keys():
    service = SERVICE.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    keys = set(re.findall(r"translate\('([^']+)'", service))

    assert keys
    assert all(key.startswith("tasks.") for key in keys)
    for key in keys:
        assert re.search(rf"'{re.escape(key)}':", catalog), f"missing todo i18n key: {key}"


def test_imported_todo_enums_are_normalized_before_storage():
    source = SERVICE.read_text(encoding="utf-8")
    assert "const TODO_STATUSES: readonly TodoStatus[]" in source
    assert "const TODO_PRIORITIES: readonly TodoPriority[]" in source
    assert "const TODO_RECURRENCES: readonly TodoRecurrence[]" in source
    assert "TODO_STATUSES.includes(todo.status as TodoStatus)" in source
    assert "TODO_PRIORITIES.includes(todo.priority as TodoPriority)" in source
    assert "TODO_RECURRENCES.includes(todo.recurrence as TodoRecurrence)" in source


def test_todo_import_validates_and_normalizes_subtasks():
    source = SERVICE.read_text(encoding="utf-8")
    assert "function normalizeSubtasks(value: unknown): TodoSubtask[]" in source
    assert "subtasks: normalizeSubtasks(todo.subtasks)" in source
    assert "candidate.subtasks !== undefined && !Array.isArray(candidate.subtasks)" in source
    assert "item.title !== 'string' || !item.title.trim()" in source
