from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_detail_editors_use_native_submit_paths():
    contracts = (
        ('class="meta-editor theme-card"', '@submit.prevent="savePlanMeta"'),
        ('class="log-editor theme-card"', '@submit.prevent="saveLog"'),
        ('class="section-editor theme-card"', '@submit.prevent="saveSection"'),
        ('class="task-editor"', '@submit.prevent="saveTask"'),
        ('class="group-editor"', '@submit.prevent="saveGroup"'),
    )

    for class_marker, submit_handler in contracts:
        editor = VIEW.split(f"<form v-if=", 1)[1] if class_marker in VIEW else ""
        assert class_marker in VIEW
        assert submit_handler in VIEW

    assert '@keyup.enter="saveLog"' not in VIEW


def test_plan_detail_editor_cancel_buttons_are_not_submit_controls():
    assert '<button type="button" class="plans-secondary" @click="editingMeta = false">' in VIEW
    assert '<button type="button" class="plans-secondary" @click="cancelTaskEdit">' in VIEW
    assert '<button type="button" class="plans-secondary" @click="cancelGroupEdit">' in VIEW
