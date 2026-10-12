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
    assert "t(priorityLabelKey(key as Priority))" in form
    assert "t('seconds', { count: 5 })" in settings


def test_legacy_icon_picker_uses_shared_translations():
    picker = (UI / "components" / "IconPicker.vue").read_text(encoding="utf-8")
    assert "useLegacyI18n" in picker
    assert "t('searchIcons')" in picker
    assert "t('customColor')" in picker


def test_legacy_priority_badges_and_expired_score_are_locale_aware():
    item = (UI / "components" / "TodoItem.vue").read_text(encoding="utf-8")
    assert ':title="t(priorityLabelKey(todo.priority))"' in item
    assert "return t('expired')" in item


def test_legacy_default_category_is_localized_only_at_display_boundary():
    i18n = (UI / "i18n.ts").read_text(encoding="utf-8")
    sidebar = (UI / "components" / "CategorySidebar.vue").read_text(encoding="utf-8")
    form = (UI / "components" / "TodoForm.vue").read_text(encoding="utf-8")
    item = (UI / "components" / "TodoItem.vue").read_text(encoding="utf-8")
    assert "defaultCategory" in i18n
    assert "translateLegacyCategoryName" in i18n
    assert "translateLegacyCategoryName(cat.id, cat.name)" in sidebar
    assert "translateLegacyCategoryName(cat.id, cat.name)" in form
    assert "translateLegacyCategoryName(category.value.id, category.value.name)" in item


def test_legacy_i18n_options_react_to_shared_locale_changes():
    i18n = (UI / "i18n.ts").read_text(encoding="utf-8")
    settings = (UI / "components" / "SettingsPanel.vue").read_text(encoding="utf-8")
    form = (UI / "components" / "TodoForm.vue").read_text(encoding="utf-8")
    assert "effilife:locale-changed" in i18n
    assert "effilife:workspace-changed" in i18n
    assert "const frequencyOptions = computed(() =>" in settings
    assert "const recurrenceOptions = computed<" in form
    assert "const warningDayOptions = computed(() =>" in form


def test_legacy_import_result_uses_locale_aware_message_and_boolean_state():
    store = (UI / "stores" / "todos.ts").read_text(encoding="utf-8")
    workspace = (UI / "views" / "TodosView.vue").read_text(encoding="utf-8")
    assert "translateLegacy('importSuccess'" in store
    assert "translateLegacy('parseJsonFailed')" in store
    assert "importSucceeded" in workspace
    assert "importMessage.includes('成功')" not in workspace

