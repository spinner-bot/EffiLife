from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_filter_tabs_expose_selected_tab_and_panel_semantics():
    assert 'class="task-tabs" role="tablist"' in TASKS
    assert TASKS.count('role="tab"') == 3
    assert TASKS.count(':aria-selected="filter ===') == 3
    assert 'id="task-list-panel" class="task-list" role="tabpanel"' in TASKS
    assert ':aria-labelledby="`tasks-tab-${filter}`"' in TASKS

