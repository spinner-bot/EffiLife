from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
LEGACY = (ROOT / "plan-helper" / "web" / "static" / "app.js").read_text(encoding="utf-8")


def test_unified_plan_workspace_uses_local_today_and_two_digit_display_parts():
    assert "const planDate = ref(toDateInput(new Date()))" in PLANS
    assert "planDate.value = toDateInput(new Date())" in PLANS
    assert "day: '2-digit'" in PLANS
    assert "String(date.getDate()).padStart(2, '0')" in PLANS


def test_legacy_plan_entry_keeps_the_same_date_contract():
    assert "String(dateArr[2]).padStart(2, '0')" in LEGACY
    assert "now.getFullYear()" in LEGACY
    assert "now.getMonth() + 1" in LEGACY
    assert "now.getDate()" in LEGACY
