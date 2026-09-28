from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_todo_tags_are_normalized_on_create_and_edit():
    source = TASKS.read_text(encoding="utf-8")
    assert "function parseTodoTags" in source
    assert "tags: parseTodoTags(tagsInput.value)" in source
    assert "tags: parseTodoTags(editingTagsInput.value)" in source
    assert "id=\"new-task-tags\"" in source
    assert "edit-tags-${todo.id}" in source
    assert "class=\"task-tag\"" in source


def test_todo_tag_labels_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.tags", "tasks.tagsPlaceholder"):
        assert source.count(f"'{key}'") == 2
