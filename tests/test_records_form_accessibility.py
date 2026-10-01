from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")


def test_record_modal_uses_native_submit_and_explicit_button_types():
    modal_form = VIEW.split('<form class="modal-form"', 1)[1].split('</form>', 1)[0]

    assert '@submit.prevent="saveRecord"' in modal_form
    assert '<button type="submit" class="btn primary"' in modal_form
    assert '<button type="button" class="close-btn"' in modal_form
    assert '<button type="button"' in modal_form
    assert '@click="saveRecord"' not in modal_form
    assert ".modal-form" in VIEW


def test_record_modal_has_focusable_dialog_semantics_and_focus_return():
    assert 'role="dialog" aria-modal="true" aria-labelledby="record-modal-title"' in VIEW
    assert 'id="record-modal-title"' in VIEW
    assert 'recordReturnFocus' in VIEW
    assert 'recordModal.value?.querySelector<HTMLElement>' in VIEW
    assert 'function onRecordModalKeydown' in VIEW
    assert '@click.self="closeForm"' in VIEW
