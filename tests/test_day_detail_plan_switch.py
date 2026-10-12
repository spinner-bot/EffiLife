from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper/desk/src/views/DayDetailView.vue").read_text(encoding="utf-8")


def test_historical_plan_switch_is_serialized_and_disables_modal_actions():
    block = VIEW.split("async function selectPlan", 1)[1].split("onMounted", 1)[0]
    assert "const changingPlan = ref(false)" in VIEW
    assert "if (changingPlan.value) return" in VIEW
    assert "changingPlan.value = true" in block
    assert "changingPlan.value = false" in block
    assert "finally" in block
    assert ":disabled=\"changingPlan\"" in VIEW
    assert "function closePlanSelector()" in VIEW
    assert "if (changingPlan.value) return" in VIEW.split("function closePlanSelector", 1)[1].split("function onPlanSelectorKeydown", 1)[0]
