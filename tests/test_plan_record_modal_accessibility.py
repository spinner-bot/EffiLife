from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_legacy_record_modal_has_dialog_and_focus_contract():
    assert 'ref="recordModal"' in VIEW
    assert 'role="dialog"' in VIEW
    assert 'aria-modal="true"' in VIEW
    assert 'aria-labelledby="legacy-record-modal-title"' in VIEW
    assert '@keydown="onRecordModalKeydown"' in VIEW
    assert "if (event.key === 'Escape')" in VIEW
    assert "recordReturnTarget" in VIEW
    assert "function closeRecordForm(force = false)" in VIEW
    assert "if (isSavingRecord.value && !force) return" in VIEW
    assert "closeRecordForm(true)" in VIEW
    assert "recordModal.value?.querySelector<HTMLElement>('button, input, select, textarea')?.focus()" in VIEW
