from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_todo_content_is_left_aligned_and_priority_stays_in_right_actions():
    assert ".task-main { min-width: 0; flex: 1; text-align: left; }" in TASKS
    assert ".task-item-actions" in TASKS
    assert "margin-left: auto" in TASKS
    assert "align-self: flex-start" in TASKS
    item_start = TASKS.index('<article v-for="todo in visibleTodos"')
    item_end = TASKS.index('<div v-if="expandedTodoId', item_start)
    item_block = TASKS[item_start:item_end]
    assert "class=\"task-rank-control\"" in item_block
    assert item_block.index("class=\"task-main\"") < item_block.index("class=\"task-item-actions\"")
