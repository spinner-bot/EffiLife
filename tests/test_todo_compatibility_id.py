from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "to-dos" / "ui" / "src" / "stores" / "todos.ts"


def test_compatibility_todo_ids_are_based_on_existing_daily_sequence_not_array_length():
    source = SOURCE.read_text(encoding="utf-8")
    assert "const datePrefix = compactNow.slice(0, 8)" in source
    assert "todo.id.match(new RegExp(`^TODO-${datePrefix}-(\\\\d+)$`))" in source
    assert "Math.max(max, value)" in source
    assert "todos.value.length + 1" not in source
