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
