from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_task_filter_tabs_expose_selected_tab_and_panel_semantics():
    assert 'class="task-tabs" role="tablist"' in TASKS
    assert TASKS.count('role="tab"') == 3
    assert TASKS.count(':aria-selected="filter ===') == 3
    assert 'id="task-list-panel" class="task-list" role="tabpanel"' in TASKS
    assert ':aria-labelledby="`tasks-tab-${filter}`"' in TASKS


def test_task_filter_tabs_support_roving_keyboard_navigation():
    assert "const taskFilters: Array<'active' | 'all' | 'completed'> = ['active', 'all', 'completed']" in TASKS
    assert 'function handleTaskTabKeydown(event: KeyboardEvent): void' in TASKS
    assert "event.key === 'ArrowRight'" in TASKS
    assert "event.key === 'ArrowLeft'" in TASKS
    assert "event.key === 'Home'" in TASKS
    assert "event.key === 'End'" in TASKS
    assert 'nextTick(() => taskTabButtons.value[nextIndex]?.focus())' in TASKS
    assert TASKS.count('ref="taskTabButtons"') == 3
