from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_frontend_has_non_destructive_legacy_todo_migration():
    source = SERVICE.read_text(encoding="utf-8")
    assert "export async function importLegacyTodoPayload" in source
    assert "normalizeImportedTodo(raw)" in source
    assert "existingIds.has(todo.id)" in source
    assert "TodoCategoryService.ensureDefaults" in source
    assert "if (migrated > 0 || categories > 0) notifyWorkspaceChanged('todos')" in source


def test_todo_normalizer_rejects_malformed_cross_module_references():
    source = SERVICE.read_text(encoding="utf-8")
    assert "candidate.related_plan_id !== undefined" in source
    assert "candidate.related_plan_task_id !== undefined" in source
    assert "candidate.related_time_record_ids.some((id) => typeof id !== 'string')" in source


def test_settings_exposes_legacy_todo_json_file_input():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "importLegacyTodoPayload" in source
    assert "accept=\".json,application/json\"" in source
    assert "openLegacyTodoImport" in source
    assert "legacyTodoImportConfirm" in source


def test_legacy_todo_migration_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "settings.archive.importLegacyTodos",
        "settings.archive.legacyTodoImportConfirm",
        "settings.archive.legacyTodoImportSuccess",
        "settings.archive.legacyTodoImportFailed",
        "tasks.legacyTodoInvalidJson",
        "tasks.legacyTodoMissingTodos",
    ):
        assert source.count(f"'{key}'") == 2
