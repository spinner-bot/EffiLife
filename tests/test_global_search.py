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
    assert "'⌘ K'" in source


def test_global_search_indexes_all_unified_data_domains():
    source = SEARCH.read_text(encoding="utf-8")
    assert "TodoService.list()" in source
    assert "listPlanSummaries()" in source
    assert "listPlanArchives()" in source
    assert "kind: 'archivedPlan'" in source
    assert "search.archivedPlanDetail" in source
    assert "archive=${encodeURIComponent(plan.file)}" in source
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
    assert "document.visibilityState === 'visible'" in source
    assert "visibilitychange" in source
    assert "WORKSPACE_CHANGED_EVENT" in events
    assert "BroadcastChannel" in events
    assert "channel?.postMessage" in events
    assert "catch" in events
    assert "Math.max(0, subscriberCount - 1)" in events
    assert "notifyWorkspaceChanged('todos')" in todo_service
    assert "notifyWorkspaceChanged('plans')" in plan_gateway
    assert "notifyWorkspaceChanged('records')" in app_store
    assert "notifyWorkspaceChanged('archive')" in archive_service


def test_global_search_surfaces_partial_index_failures_and_can_retry():
    source = SEARCH.read_text(encoding="utf-8")
    assert "const indexUnavailable = ref(false)" in source
    assert "const indexPartial = ref(false)" in source
    assert "failedSources" in source
    assert "planArchivesState.value === 'unavailable'" in source
    assert 'class="search-state search-error" role="status" aria-live="polite"' in source
    assert 'class="search-partial" role="status" aria-live="polite"' in source
    assert "async function retryIndex(): Promise<void>" in source
    assert "search.partial" in I18N.read_text(encoding="utf-8")


def test_global_search_detail_separators_are_localized():
    source = SEARCH.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    assert "search.detailSeparator" in source
    assert "{{ t('search.detailSeparator') }}" in source
    assert catalog.count("'search.detailSeparator':") == 2


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
    assert "event.key === 'Home'" in source
    assert "event.key === 'End'" in source
    assert "openResult(filteredResults.value[selectedIndex.value])" in source
    assert "class=\"search-result\" :class=\"{ selected: selectedIndex === index }\"" in source


def test_global_search_keeps_selected_result_visible():
    source = SEARCH.read_text(encoding="utf-8")
    assert "scrollIntoView({ block: 'nearest' })" in source
    assert "watch(\n  [selectedIndex, () => filteredResults.value.length]" in source


def test_global_search_exposes_active_result_to_assistive_technology():
    source = SEARCH.read_text(encoding="utf-8")
    assert "role=\"combobox\"" in source
    assert 'aria-activedescendant="filteredResults.length ? resultDomId(filteredResults[selectedIndex]) : undefined"' in source
    assert 'id="global-search-results" class="search-results" role="listbox"' in source
    assert 'role="option"' in source
    assert "function resultDomId(result: SearchResult)" in source


def test_global_search_trigger_and_dialog_are_explicitly_linked():
    app = APP.read_text(encoding="utf-8")
    source = SEARCH.read_text(encoding="utf-8")
    assert 'id="global-search-trigger"' in app
    assert 'aria-haspopup="dialog"' in app
    assert ':aria-expanded="showGlobalSearch"' in app
    assert 'aria-controls="global-search-dialog"' in app
    assert 'id="global-search-dialog"' in source
    assert 'aria-labelledby="global-search-title"' in source
    assert 'id="global-search-title"' in source


def test_global_search_traps_tab_focus_and_restores_trigger_focus():
    source = SEARCH.read_text(encoding="utf-8")
    assert "const dialog = ref<HTMLElement | null>(null)" in source
    assert "let returnFocus: HTMLElement | null = null" in source
    assert "function handleDialogKeydown(event: KeyboardEvent)" in source
    assert "event.key !== 'Tab'" in source
    assert "returnFocus?.isConnected" in source
    assert 'ref="dialog"' in source
    assert '@keydown="handleDialogKeydown"' in source


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
        "search.archivedPlanDetail",
        "search.planTaskDetail",
        "search.module.todo",
        "search.module.plan",
        "search.module.archivedPlan",
        "search.module.planTask",
        "search.module.record",
    ):
        assert source.count(f"'{key}'") == 2


def test_global_search_labels_each_result_with_its_source_module():
    source = SEARCH.read_text(encoding="utf-8")
    assert "function searchModuleLabel(kind: SearchResult['kind'])" in source
    assert "search.module.todo" in source
    assert "search.module.plan" in source
    assert "search.module.archivedPlan" in source
    assert "search.module.planTask" in source
    assert "search.module.record" in source
    assert "searchModuleLabel(result.kind)" in source
