from pathlib import Path


SOURCE = Path("time-helper/desk/src/views/PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_create_dialog_has_standard_dialog_semantics():
    assert 'role="dialog"' in SOURCE
    assert 'aria-modal="true"' in SOURCE
    assert 'aria-labelledby="plan-create-title"' in SOURCE
    assert 'id="plan-create-title"' in SOURCE


def test_plan_create_dialog_supports_keyboard_and_backdrop_close():
    assert '@click.self="void closeCreatePlan()"' in SOURCE
    assert '@keydown="onCreateModalKeydown"' in SOURCE
    assert "event.key === 'Escape'" in SOURCE
    assert '@click="void closeCreatePlan()"' in SOURCE


def test_plan_create_dialog_does_not_close_during_create_but_force_closes_after_success():
    assert "function closeCreatePlan(force = false)" in SOURCE
    assert "if (isLoading.value && !force) return" in SOURCE
    assert "closeCreatePlan(true)" in SOURCE
    assert ':disabled="isLoading" @click="void closeCreatePlan()"' in SOURCE
    assert "isCreatePlanDirty()" in SOURCE
    assert "plans.discardCreateConfirm" in SOURCE


def test_plan_create_dialog_focuses_name_and_returns_focus_after_close():
    assert 'const createNameInput = ref<HTMLInputElement | null>(null)' in SOURCE
    assert 'createNameInput.value?.focus()' in SOURCE
    assert 'createReturnFocus.value = document.activeElement instanceof HTMLElement' in SOURCE
    assert 'if (returnTarget?.isConnected) returnTarget.focus()' in SOURCE
