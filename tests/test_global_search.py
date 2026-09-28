from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "time-helper" / "desk" / "src" / "App.vue"
SEARCH = ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_global_search_is_available_from_app_shell():
    source = APP.read_text(encoding="utf-8")
    assert "GlobalSearch" in source
    assert "Ctrl" not in source or "onGlobalKeydown" in source
    assert "event.metaKey" in source
    assert "event.ctrlKey" in source
    assert "global-search-trigger" in source


def test_global_search_indexes_all_unified_data_domains():
    source = SEARCH.read_text(encoding="utf-8")
    assert "TodoService.list()" in source
    assert "listPlanSummaries()" in source
    assert "STORE_NAMES.RECORDS" in source
    assert "router.push(result.route)" in source


def test_global_search_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in (
        "search.open",
        "search.title",
        "search.close",
        "search.placeholder",
        "search.loading",
        "search.empty",
        "search.hint",
        "search.todoDetail",
        "search.planDetail",
    ):
        assert source.count(f"'{key}'") == 2
