from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_default_category_is_localized_only_at_display_boundary():
    source = VIEW.read_text(encoding="utf-8")
    assert "function categoryLabel(item: Pick<TodoCategory, 'id' | 'name'>): string" in source
    assert "item.id === 'default'" in source
    assert "t('tasks.defaultCategory')" in source
    assert "categoryLabel(item)" in source


def test_default_category_translation_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'tasks.defaultCategory'") == 2
