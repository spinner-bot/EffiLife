from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_td_search_filters_single_todos_without_crossing_into_ph():
    assert "const taskSearch = ref('')" in TASKS
    assert "todo.title} ${todo.description || ''} ${(todo.tags || []).join(' ')" in TASKS
    assert 'v-model="taskSearch"' in TASKS
    assert 'type="search"' in TASKS


def test_td_search_is_localized_and_keeps_existing_status_category_filters():
    assert "const categoryFilter = ref('')" in TASKS
    assert "const filter = ref<'all' | 'active' | 'completed'>('active')" in TASKS
    assert I18N.count("'tasks.searchLabel'") == 2
    assert I18N.count("'tasks.searchPlaceholder'") == 2
