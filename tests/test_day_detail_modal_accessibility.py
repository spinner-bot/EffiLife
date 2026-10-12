from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue").read_text(encoding="utf-8")


def test_day_plan_selector_modal_has_dialog_and_focus_contract():
    assert 'ref="planSelectorModal"' in VIEW
    assert 'role="dialog"' in VIEW
    assert 'aria-modal="true"' in VIEW
    assert 'aria-labelledby="day-plan-selector-title"' in VIEW
    assert '@keydown="onPlanSelectorKeydown"' in VIEW
    assert "if (event.key === 'Escape')" in VIEW
    assert "planSelectorReturnTarget" in VIEW
    assert "function closePlanSelector()" in VIEW
    assert "planSelectorModal.value?.querySelector<HTMLElement>('button, input, select, textarea')?.focus()" in VIEW
