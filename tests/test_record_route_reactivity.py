from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_records_view_reacts_to_reused_todo_deep_links():
    assert "import { ref, computed, onMounted, onUnmounted, watch } from 'vue'" in SOURCE
    assert "function preselectLinkedTodo(): void" in SOURCE
    assert "watch(linkedTodoFromQuery" in SOURCE
    assert "preselectLinkedTodo()" in SOURCE


def test_records_view_does_not_preselect_unknown_todos():
    assert "const todoId = linkedTodoFromQuery.value" in SOURCE
    assert "todos.value.some((todo) => todo.id === todoId)" in SOURCE
