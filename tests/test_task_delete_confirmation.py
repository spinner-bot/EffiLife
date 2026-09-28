from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_deletion_requires_a_localized_confirmation():
    source = TASK_VIEW.read_text(encoding="utf-8")
    assert "requestConfirm(t('tasks.deleteConfirm'), { tone: 'danger' })" in source
    host = (ROOT / "time-helper" / "desk" / "src" / "components" / "ConfirmHost.vue").read_text(encoding="utf-8")
    assert "common.confirmTitle" in host
    assert "common.cancel" in host


def test_task_delete_confirmation_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'tasks.deleteConfirm'") == 2


def test_task_deletion_reports_success():
    source = TASK_VIEW.read_text(encoding="utf-8")
    assert "notifyToast(t('tasks.deleted'), 'success')" in source
