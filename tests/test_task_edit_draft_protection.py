from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_task_edit_cancel_protects_unsaved_changes():
    assert "type TodoEditDraft =" in VIEW
    assert "function isEditDirty(): boolean" in VIEW
    assert "async function cancelEdit(force = false): Promise<void>" in VIEW
    assert "t('tasks.discardEditConfirm')" in VIEW
    assert '@click="void cancelEdit()"' in VIEW
    assert "await cancelEdit(true)" in VIEW


def test_task_edit_discard_confirmation_is_localized():
    assert "'tasks.discardEditConfirm': '当前待办有未保存的修改，确定放弃吗？'" in I18N
    assert "'tasks.discardEditConfirm': 'This task has unsaved changes. Discard them?'" in I18N
