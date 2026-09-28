from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "time-helper" / "desk" / "src" / "storage" / "recovery.ts"


def test_emergency_backup_contains_and_restores_unified_todos():
    source = RECOVERY.read_text(encoding="utf-8")
    assert "getRawAll(STORE_NAMES.TODOS)" in source
    assert "getRawAll(STORE_NAMES.TODO_CATEGORIES)" in source
    assert "backupData.todos" in source
    assert "backupData.todoCategories" in source
    assert "if (Array.isArray(data.todos))" in source
    assert "clear(STORE_NAMES.TODOS)" in source
    assert "putRaw(STORE_NAMES.TODOS, todo)" in source
    assert "if (Array.isArray(data.todoCategories))" in source
    assert "putRaw(STORE_NAMES.TODO_CATEGORIES, category)" in source
    assert "notifyWorkspaceChanged('archive')" in source

