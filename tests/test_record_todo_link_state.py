from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_records_do_not_offer_a_dead_todo_deeplink_after_a_successful_load():
    source = VIEW.read_text(encoding="utf-8")
    assert "const todoOptionsLoaded = ref(false)" in source
    assert "function isLinkedTodoUnavailable(todoId: string): boolean" in source
    assert "if (todoOptionsLoaded.value && !todoTitleById.value.has(todoId)) return" in source
    assert ':disabled="isLinkedTodoUnavailable(record.todo_id)"' in source
    assert "records.todoUnavailable" in source


def test_records_keep_links_non_destructive_when_todo_storage_is_unavailable():
    source = VIEW.read_text(encoding="utf-8")
    load_block = source.split("async function loadTodoOptions", 1)[1].split("let stopWorkspaceListener", 1)[0]
    assert "todoOptionsUnavailable.value = true" in load_block
    assert "todoOptionsLoaded.value = false" in load_block
    assert I18N.read_text(encoding="utf-8").count("'records.todoUnavailable':") == 2
