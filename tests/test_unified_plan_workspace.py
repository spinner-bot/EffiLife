from pathlib import Path


HUB = Path("time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")
DAILY = Path("time-helper/desk/src/views/PlanView.vue").read_text(encoding="utf-8")


def test_default_plan_hub_embeds_daily_workspace_and_event_workspace_together():
    assert '<DailyPlanView :embedded="true" />' in HUB
    assert 'unified-plan-section event-plans-section' in HUB
    assert 'class="plan-domain-grid"' not in HUB


def test_daily_plan_supports_embedded_mode_without_duplicate_header():
    assert "defineProps<{ embedded?: boolean }>()" in DAILY
    assert 'class="plan-view" :class="{ embedded: props.embedded }"' in DAILY
    assert '<header v-if="!props.embedded" class="pv-header">' in DAILY
