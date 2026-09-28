from pathlib import Path


APP_SOURCE = Path("plan-helper/web/static/app.js").read_text(encoding="utf-8")
HTML_SOURCE = Path("plan-helper/web/index.html").read_text(encoding="utf-8")
STYLE_SOURCE = Path("plan-helper/web/static/styles.css").read_text(encoding="utf-8")


def _create_block() -> str:
    start = HTML_SOURCE.index("<!-- Create Plan Modal -->")
    end = HTML_SOURCE.index("<!-- Edit Plan Modal -->")
    return HTML_SOURCE[start:end]


def test_legacy_create_flow_starts_with_empty_plan():
    open_start = APP_SOURCE.index("function openCreatePlan()")
    create_start = APP_SOURCE.index("async function createPlan()", open_start)
    open_block = APP_SOURCE[open_start:create_start]
    assert "newPlan.sections = [];" in open_block
    assert "newPlan.sections = [newSection()]" not in open_block


def test_legacy_create_dialog_only_collects_name_and_date():
    block = _create_block()
    assert 'v-model="newPlan.name"' in block
    assert 'v-model="newPlan.date"' in block
    assert "newPlan.sections" not in block
    assert "创建后将进入全屏编辑器" in block


def test_legacy_plan_editor_is_fullscreen_and_keyboard_dismissible():
    edit_start = HTML_SOURCE.index("<!-- Edit Plan Modal -->")
    edit_end = HTML_SOURCE.index("<!-- Settings Modal -->", edit_start)
    edit_block = HTML_SOURCE[edit_start:edit_end]
    assert "modal-fullscreen" in edit_block
    assert 'role="dialog"' in edit_block
    assert '@keydown.esc="closeEditPlan"' in edit_block
    assert ".modal-fullscreen" in STYLE_SOURCE
    assert ".modal-fullscreen .modal-body" in STYLE_SOURCE
