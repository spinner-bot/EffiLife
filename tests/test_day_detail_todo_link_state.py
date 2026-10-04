from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_day_detail_does_not_offer_dead_todo_deeplinks_after_loading_references():
    source = VIEW.read_text(encoding="utf-8")
    assert "async function loadTodoReferences(): Promise<void>" in source
    assert "function isLinkedTodoUnavailable(todoId?: string): boolean" in source
    assert "if (todoId && !isLinkedTodoUnavailable(todoId))" in source
    assert ':disabled="isLinkedTodoUnavailable(record.todo_id)"' in source
    assert "dayDetail.todoUnavailable" in source


def test_day_detail_keeps_todo_references_when_todo_storage_is_unavailable():
    source = VIEW.read_text(encoding="utf-8")
    block = source.split("async function loadTodoReferences", 1)[1].split("function isLinkedTodoUnavailable", 1)[0]
    assert "todoReferencesLoaded.value = false" in block
    assert I18N.read_text(encoding="utf-8").count("'dayDetail.todoUnavailable':") == 2


def test_day_detail_reloads_when_route_date_or_workspace_todos_change():
    source = VIEW.read_text(encoding="utf-8")
    assert "watch(dateStr, () =>" in source
    assert "const stopWorkspaceListener = onWorkspaceChanged" in source
    assert "source === 'todos' || source === 'archive'" in source
    assert "stopWorkspaceListener()" in source


def test_day_detail_ignores_stale_async_route_responses():
    source = VIEW.read_text(encoding="utf-8")
    assert "let loadRequestId = 0" in source
    assert "const requestId = ++loadRequestId" in source
    assert "const [statResult, recordsResult, planResult] = await Promise.allSettled([" in source
    assert "if (statResult.status === 'rejected')" in source
    assert "if (recordsResult.status === 'rejected')" in source
    assert "if (requestId !== loadRequestId) return" in source
