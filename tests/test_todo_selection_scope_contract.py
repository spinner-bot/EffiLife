from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")


def test_bulk_selection_is_scoped_to_current_view_and_reconciled_after_reload():
    assert "function reconcileTodoSelection(): void" in VIEW
    assert "const availableIds = new Set(todos.value.map((todo) => todo.id))" in VIEW
    assert "watch(\n  () => [filter.value, categoryFilter.value, taskSearch.value]," in VIEW
    assert "todos.value = await TodoService.list()\n    reconcileTodoSelection()" in VIEW
    assert "todos.value = todos.value.filter((item) => item.id !== todo.id)\n    reconcileTodoSelection()" in VIEW
