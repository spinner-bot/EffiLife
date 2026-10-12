from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_date_inputs_default_to_today_and_display_two_digit_day():
    assert "const planDate = ref(toDateInput(new Date()))" in PLANS
    assert "const templateDraftDate = ref(toDateInput(new Date()))" in PLANS
    assert "planDate.value = toDateInput(new Date())" in PLANS
    assert "templateDraftDate.value = toDateInput(new Date())" in PLANS

    format_block = PLANS.split("function formatPlanDate", 1)[1].split("function formatLogTime", 1)[0]
    assert "year: 'numeric'" in format_block
    assert "month: '2-digit'" in format_block
    assert "day: '2-digit'" in format_block
    assert "parseLocalDate(`${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`)" in format_block
    assert "if (Number.isNaN(value.getTime())) return ''" in format_block


def test_plan_date_editor_uses_native_calendar_date_inputs():
    assert PLANS.count('v-model="templateDraftDate" type="date"') == 1
    assert PLANS.count('v-model="planDate" type="date"') >= 2
