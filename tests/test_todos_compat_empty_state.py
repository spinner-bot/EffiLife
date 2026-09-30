from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "to-dos" / "ui" / "src" / "stores" / "todos.ts"


def test_legacy_todo_ui_starts_without_demo_items_or_business_categories():
    source = STORE.read_text(encoding="utf-8")

    assert "const todos = ref<Todo[]>([])" in source
    assert "const categories = ref<Category[]>([{ ...defaultCategory }])" in source
    assert "mockTodos" not in source
    assert "mockCategories" not in source


def test_legacy_todo_ui_preserves_imported_categories_and_fallback_default():
    source = STORE.read_text(encoding="utf-8")

    assert "Array.isArray(data.categories)" in source
    assert "data.categories.length ? data.categories : [{ ...defaultCategory }]" in source
    assert "if (data.todos) todos.value = data.todos" in source
