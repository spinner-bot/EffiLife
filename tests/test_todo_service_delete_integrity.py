from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"


def test_todo_service_delete_cleans_time_record_reverse_links():
    source = SERVICE.read_text(encoding="utf-8")
    assert "import { DataService } from './dataService'" in source
    remove_block = source.split("async remove(id: string): Promise<void>", 1)[1].split("async trackTime", 1)[0]
    assert "await DataService.unlinkTodoFromRecords(id)" in remove_block
    assert "await deleteRaw(STORE_NAMES.TODOS, id)" in remove_block
    assert remove_block.index("await DataService.unlinkTodoFromRecords(id)") < remove_block.index("await deleteRaw(STORE_NAMES.TODOS, id)")
    assert "console.warn('Failed to clean deleted todo record links:', error)" in remove_block
