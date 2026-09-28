from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_deletion_requires_a_localized_confirmation():
    source = TASK_VIEW.read_text(encoding="utf-8")
    assert "if (!confirm(t('tasks.deleteConfirm'))) return" in source


def test_task_delete_confirmation_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'tasks.deleteConfirm'") == 2
