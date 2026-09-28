from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
SEARCH = ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_global_search_is_available_from_app_shell():
    source = APP.read_text(encoding="utf-8")
    assert "GlobalSearch" in source
    assert "Ctrl" not in source or "onGlobalKeydown" in source
    assert "event.metaKey" in source
    assert "event.ctrlKey" in source
    assert "searchShortcut" in source
    assert "Mac|iPhone|iPad" in source
    assert "global-search-trigger" in source


def test_global_search_indexes_all_unified_data_domains():
    source = SEARCH.read_text(encoding="utf-8")
    assert "TodoService.list()" in source
    assert "listPlanSummaries()" in source
    assert "STORE_NAMES.RECORDS" in source
    assert "router.push(result.route)" in source
    assert "tasks?todo=" in source
    assert "plans?plan=" in source


def test_global_search_refreshes_when_unified_data_changes():
    source = SEARCH.read_text(encoding="utf-8")
    events = (ROOT / "time-helper" / "desk" / "src" / "services" / "workspaceEvents.ts").read_text(encoding="utf-8")
    todo_service = (ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts").read_text(encoding="utf-8")
    plan_gateway = (ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts").read_text(encoding="utf-8")
    app_store = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")
    archive_service = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    assert "onWorkspaceChanged" in source
    assert "if (props.open) void loadIndex()" in source
    assert "WORKSPACE_CHANGED_EVENT" in events
    assert "BroadcastChannel" in events
    assert "channel?.postMessage" in events
    assert "catch" in events
    assert "Math.max(0, subscriberCount - 1)" in events
    assert "notifyWorkspaceChanged('todos')" in todo_service
    assert "notifyWorkspaceChanged('plans')" in plan_gateway
    assert "notifyWorkspaceChanged('records')" in app_store
    assert "notifyWorkspaceChanged('archive')" in archive_service


def test_search_targets_are_consumed_by_plan_and_task_views():
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    tasks = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
    assert "route.query.plan" in plans
    assert "openPlan(target)" in plans
    assert "route.query.todo" in tasks
    assert "scrollIntoView" in tasks


def test_global_search_supports_keyboard_result_navigation():
    source = SEARCH.read_text(encoding="utf-8")
    assert "selectedIndex" in source
    assert "ArrowDown" in source
    assert "ArrowUp" in source
    assert "openResult(filteredResults.value[selectedIndex.value])" in source
    assert "class=\"search-result\" :class=\"{ selected: selectedIndex === index }\"" in source


def test_global_search_exposes_active_result_to_assistive_technology():
    source = SEARCH.read_text(encoding="utf-8")
    assert "role=\"combobox\"" in source
    assert 'aria-activedescendant="filteredResults.length ? resultDomId(filteredResults[selectedIndex]) : undefined"' in source
    assert 'id="global-search-results" class="search-results" role="listbox"' in source
    assert 'role="option"' in source
    assert "function resultDomId(result: SearchResult)" in source


def test_global_search_indexes_todo_descriptions_and_tags():
    source = SEARCH.read_text(encoding="utf-8")
    assert "todo.description || todo.tags?.join(', ')" in source
    assert "searchText: `${todo.description || ''} ${(todo.tags || []).join(' ')}`" in source
    assert "result.searchText" in source


def test_global_search_indexes_plan_tasks_and_deep_links():
    source = SEARCH.read_text(encoding="utf-8")
    plans = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
    assert "getPlanTasks" in source
    assert "kind: 'planTask'" in source
    assert "&task=${encodeURIComponent(task.internal_id)}" in source
    assert "route.query.task" in plans
    assert "plan-task-${task.internal_id}" in plans


def test_global_search_targets_a_specific_time_record():
    source = SEARCH.read_text(encoding="utf-8")
    day = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")
    assert "?record=${encodeURIComponent(record.id || `${record.date}-${index}`)}" in source
    assert "route.query.record" in day
    assert "record-search-target" in day
    assert "openLinkedTodo" in day


def test_global_search_prioritizes_title_matches():
    source = SEARCH.read_text(encoding="utf-8")
    assert "title === normalized" in source
    assert "title.startsWith(normalized)" in source
    assert ".sort((left, right) => right.score - left.score" in source


def test_global_search_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "search.open",
        "search.title",
        "search.close",
        "search.placeholder",
        "search.loading",
        "search.empty",
        "search.hint",
        "search.results",
        "search.todoDetail",
        "search.planDetail",
        "search.planTaskDetail",
    ):
        assert source.count(f"'{key}'") == 2
