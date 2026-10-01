from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_td_refreshes_after_archive_import_and_network_recovery():
    assert "if (!source || !['todos', 'records', 'settings', 'archive', 'network'].includes(source)) return" in TASKS
    assert "await loadTodos()" in TASKS
    assert "await loadCategories()" in TASKS
