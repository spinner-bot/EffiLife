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


def test_legacy_todo_list_and_item_use_shared_translations():
    todo_list = (UI / "components" / "TodoList.vue").read_text(encoding="utf-8")
    todo_item = (UI / "components" / "TodoItem.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in todo_list
    assert "t('emptyTitle')" in todo_list
    assert "t('completed')" in todo_list
    assert "useLegacyI18n" in todo_item
    assert "t('dueToday')" in todo_item
    assert "t('moreActions')" in todo_item


def test_legacy_form_and_settings_use_shared_translations():
    form = (UI / "components" / "TodoForm.vue").read_text(encoding="utf-8")
    settings = (UI / "components" / "SettingsPanel.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in form
    assert "t('titlePlaceholder')" in form
    assert "t('deadlineReminder')" in form
    assert "useLegacyI18n" in settings
    assert "t('scoreFrequency')" in settings


def test_legacy_icon_picker_uses_shared_translations():
    picker = (UI / "components" / "IconPicker.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in picker
    assert "t('searchIcons')" in picker
    assert "t('customColor')" in picker

