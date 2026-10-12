from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "to-dos" / "ui" / "src"


def test_legacy_todo_ui_has_a_shared_locale_contract():
    source = (UI / "i18n.ts").read_text(encoding="utf-8")
    assert "export type LegacyLocale = 'zh-CN' | 'en-US'" in source
    assert "efflife_locale" in source
    assert "export function useLegacyI18n()" in source


def test_legacy_filter_and_sidebar_use_shared_translations():
    filter_bar = (UI / "components" / "FilterBar.vue").read_text(encoding="utf-8")
    sidebar = (UI / "components" / "CategorySidebar.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in filter_bar
    assert "useLegacyI18n" in sidebar
    assert "t('filter')" in filter_bar
    assert "t('todoTitle')" in sidebar
    assert "t('completionRate')" in sidebar


def test_legacy_workspace_controls_use_shared_translations():
    workspace = (UI / "views" / "TodosView.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in workspace
    for key in ("searchPlaceholder", "newTodo", "importData", "exportJson", "completeAction"):
        assert f"t('{key}')" in workspace

