from pathlib import Path


HUB = Path("time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
DAILY = Path("time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")


def test_plan_workspace_keeps_daily_time_management_out_of_ph():
    assert '<DailyPlanView :embedded="true" />' not in HUB
    assert 'unified-plan-section event-plans-section' not in HUB
    assert "'plans-content-hub': view === 'hub'" not in HUB
    assert 'class="plan-domain-grid"' not in HUB


def test_desktop_plan_hub_uses_single_ph_workspace_layout():
    assert "@media (min-width: 1100px)" in HUB
    assert ".plans-content-hub .event-plans-section" not in HUB


def test_daily_plan_supports_embedded_mode_without_duplicate_header():
    assert "defineProps<{ embedded?: boolean }>()" in DAILY
    assert 'class="plan-view" :class="{ embedded: props.embedded }"' in DAILY
    assert '<header v-if="!props.embedded" class="pv-header">' in DAILY


def test_plan_hub_recovers_when_another_window_archives_the_open_plan():
    assert "if (selectedPlan.value && (source === 'plans' || source === 'archive' || source === 'network'))" in HUB
    assert "Keep the last known plan visible during a transient service or" in HUB
    assert "detailRefreshUnavailable.value = true" in HUB
    assert "v-if=\"detailRefreshUnavailable\"" in HUB
    assert "@click=\"retryPlanService\"" in HUB


def test_plan_hub_explains_and_restores_archived_plan_deep_links():
    assert "const archivedPlanTarget = computed" in HUB
    assert "archive.plan_id" in HUB
    assert "plans.archivedTargetTitle" in HUB
    assert "@click=\"restoreArchive(archivedPlanTarget)\"" in HUB
    assert "await revealSearchTarget()" in HUB


def test_plan_creation_collects_initial_sections_and_tasks_before_writing():
    assert "const createSections = ref<InitialPlanSection[]>([])" in HUB
    assert "createSections.value = [{ name: '', info: '', tasks: [{ content: '', time_minutes: 0 }] }]" in HUB
    assert "createEventPlan(name, toDateTuple(planDate.value), sections)" in HUB
    assert "plans.createTaskRequired" in HUB
    assert "v-for=\"(task, taskIndex) in section.tasks\"" in HUB


def test_plan_creation_uses_ph_section_lettering_beyond_z():
    assert "function sectionDisplayLetter(index: number): string" in HUB
    assert "value = Math.floor(value / 26) - 1" in HUB
    assert "sectionDisplayLetter(sectionIndex)" in HUB
