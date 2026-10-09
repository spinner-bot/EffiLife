from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_home_summary_aggregates_three_unified_workstreams():
    assert "const todayRecordHours = computed(() => appStore.todayRecords.reduce" in HOME
    assert 'class="workflow-summary"' in HOME
    assert "home.timeModuleSummary" in HOME
    assert "home.planModuleSummary" in HOME
    assert "home.todoModuleSummary" in HOME
    assert "function openWorkflowSummary(module: WorkflowSummaryModule): void" in HOME
    assert "openWorkflowSummary('time')" in HOME
    assert "openWorkflowSummary('plans')" in HOME
    assert "openWorkflowSummary('todos')" in HOME


def test_home_ignores_invalid_time_record_durations_in_summary():
    assert "const duration = Number(record.duration)" in HOME
    assert "Number.isFinite(duration) && duration >= 0" in HOME


def test_home_workflow_summary_has_bilingual_copy():
    for key in ("home.workflowSummary", "home.timeModuleSummary", "home.planModuleSummary", "home.todoModuleSummary"):
        assert I18N.count(f"'{key}':") == 2


def test_home_empty_plan_action_enters_plan_helper_workspace():
    assert 'action-route="/plans"' in HOME
    assert 'action-route="/plan"' not in HOME


def test_home_does_not_duplicate_the_shell_branding():
    template = HOME.split("<template>", 1)[1].split("</template>", 1)[0]
    assert 'class="logo"' not in template
    assert "justify-content: flex-end" in HOME


def test_home_plan_service_failure_has_an_explicit_desktop_retry():
    assert "refreshEventPlanSummary" in HOME
    assert "home.retryEventPlans" in HOME
    assert 'v-if="!mobilePlanRuntime"' in HOME
    assert "event-overview-retry" in HOME
    assert I18N.count("'home.retryEventPlans':") == 2


def test_home_time_summary_failure_has_an_explicit_retry_without_fake_empty_state():
    assert "const timeSummaryUnavailable = ref(false)" in HOME
    assert "async function refreshTimeSummary(): Promise<void>" in HOME
    assert "timeSummaryUnavailable.value = true" in HOME
    assert 'class="stats-unavailable" role="status" aria-live="polite"' in HOME
    assert '@click="refreshTimeSummary"' in HOME
    assert I18N.count("'home.timeUnavailable':") == 2
    assert I18N.count("'home.retryTime':") == 2


def test_home_workflow_summary_does_not_turn_unavailable_data_into_zero_values():
    assert "'is-unavailable': timeSummaryUnavailable" in HOME
    assert "timeSummaryUnavailable ? '—' : hoursToHm(todayRecordHours, locale)" in HOME
    assert "eventPlanState === 'unavailable' ? '—'" in HOME
    assert "todoSummaryUnavailable ? '—' : activeTodoCount" in HOME


def test_home_unavailable_summary_cards_retry_in_place_before_navigating():
    assert "if (timeSummaryUnavailable.value)" in HOME
    assert "void refreshTimeSummary()" in HOME
    assert "if (eventPlanState.value === 'unavailable' and !mobilePlanRuntime)" not in HOME
    assert "if (eventPlanState.value === 'unavailable' && !mobilePlanRuntime)" in HOME
    assert "void refreshEventPlanSummary()" in HOME
    assert "if (todoSummaryUnavailable.value)" in HOME
    assert "void refreshTodoSummary()" in HOME


def test_home_inbox_has_dialog_semantics_and_escape_focus_return():
    assert 'aria-haspopup="dialog"' in HOME
    assert 'aria-controls="home-inbox-panel"' in HOME
    assert 'id="home-inbox-panel"' in HOME
    assert 'role="dialog"' in HOME
    assert 'aria-labelledby="home-inbox-title"' in HOME
    assert 'closeInboxPanel(true)' in HOME
    assert 'inboxButton.value?.focus()' in HOME


def test_home_inbox_traps_tab_focus_inside_open_panel():
    assert "const inboxPanel = ref<HTMLElement | null>(null)" in HOME
    assert 'ref="inboxPanel"' in HOME
    assert "event.key !== 'Tab' || !inboxPanel.value" in HOME
    assert "inboxPanel.value.querySelectorAll<HTMLElement>" in HOME
    assert "event.shiftKey && document.activeElement === first" in HOME
    assert "!event.shiftKey && document.activeElement === last" in HOME


def test_home_tablet_uses_horizontal_workbench_between_mobile_and_desktop_breakpoints():
    tablet = "@media (min-width: 681px) and (max-width: 899px)"
    assert tablet in HOME
    tablet_block = HOME.split(tablet, 1)[1].split(".stats-header-row", 1)[0]
    assert "max-width: 900px" in tablet_block
    assert "display: grid;" in tablet_block
    assert "grid-template-columns: minmax(190px, .46fr) minmax(0, 1.54fr);" in tablet_block
    assert "grid-row: 1 / span 4;" in tablet_block
    assert ".stats-section," in tablet_block
    assert "align-items: stretch" in tablet_block
    assert "text-align: left;" in tablet_block


def test_home_serializes_summary_refreshes_and_queues_external_changes():
    assert "let summaryRefreshRunning = false" in HOME
    assert "let summaryRefreshQueued = false" in HOME
    assert "async function refreshWorkspaceSummaries(): Promise<void>" in HOME
    assert "if (summaryRefreshRunning)" in HOME
    assert "summaryRefreshQueued = true" in HOME
    assert "} while (summaryRefreshQueued)" in HOME
    assert "refreshTimer = window.setInterval(() => { void refreshWorkspaceSummaries() }, 60000)" in HOME


def test_home_exposes_one_accessible_refresh_for_all_workspace_summaries():
    assert "const workspaceRefreshing = ref(false)" in HOME
    assert "void refreshWorkspaceSummaries()" in HOME
    assert ':aria-label="t(\'home.refreshWorkspace\')"' in HOME
    assert ':aria-busy="workspaceRefreshing"' in HOME
    assert 'class="workspace-refresh-btn"' in HOME
    assert I18N.count("'home.refreshWorkspace':") == 2


def test_home_discloses_the_last_completed_summary_sync_time_without_persisting_it():
    assert "const lastWorkspaceRefreshAt = ref<number | null>(null)" in HOME
    assert "lastWorkspaceRefreshAt.value = Date.now()" in HOME
    assert "function formatWorkspaceRefreshTime(timestamp: number | null): string" in HOME
    assert "toLocaleTimeString(locale.value" in HOME
    assert "t('home.lastRefreshed', { time: formatWorkspaceRefreshTime(lastWorkspaceRefreshAt) })" in HOME
    assert 'class="workspace-refresh-status" role="status"' in HOME
    assert I18N.count("'home.lastRefreshed':") == 2


def test_home_discards_stale_todo_and_plan_summary_responses():
    assert "let todoSummaryRequestId = 0" in HOME
    assert "let eventPlanSummaryRequestId = 0" in HOME
    assert "const requestId = ++todoSummaryRequestId" in HOME
    assert "if (requestId !== todoSummaryRequestId) return" in HOME
    assert "const requestId = ++eventPlanSummaryRequestId" in HOME
    assert "if (requestId !== eventPlanSummaryRequestId) return" in HOME
