from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "to-dos" / "ui" / "src" / "stores" / "todos.ts"
VIEW = ROOT / "to-dos" / "ui" / "src" / "views" / "TodosView.vue"


def test_legacy_todo_today_filter_uses_local_calendar_date():
    source = STORE.read_text(encoding="utf-8")
    assert "function localDateKey(date: Date = new Date()): string" in source
    assert "const today = localDateKey()" in source
    assert "new Date().toISOString().split('T')[0]" not in source


def test_legacy_todo_backup_filename_uses_local_calendar_date():
    source = VIEW.read_text(encoding="utf-8")
    assert "const localDate = `${now.getFullYear()}-" in source
    assert "todos-backup-${localDate}.json" in source
    assert "todos-backup-${new Date().toISOString().slice(0, 10)}.json" not in source
