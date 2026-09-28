from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_description_is_available_for_create_and_edit():
    source = TASKS.read_text(encoding="utf-8")
    assert "description: description.value" in source
    assert "description: editingDescription.value" in source
    assert "id=\"new-task-description\"" in source
    assert "edit-description-${todo.id}" in source
    assert "todo.description" in source


def test_task_description_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.description", "tasks.descriptionPlaceholder"):
        assert source.count(f"'{key}'") == 2
