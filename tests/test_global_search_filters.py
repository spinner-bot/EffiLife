from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_global_search_filters_keep_module_domains_explicit():
    assert "type SearchFilter = 'all' | 'th' | 'ph' | 'td'" in SOURCE
    assert "result.kind === 'record'" in SOURCE
    assert "result.kind === 'todo'" in SOURCE
    assert "result.kind === 'plan' || result.kind === 'planTask' || result.kind === 'archivedPlan'" in SOURCE
    assert "resultMatchesFilter(result)" in SOURCE


def test_global_search_filters_are_localized_in_both_catalogs():
    for key in (
        "search.filterLabel",
        "search.filter.all",
        "search.filter.th",
        "search.filter.ph",
        "search.filter.td",
    ):
        assert I18N.count(f"'{key}':") == 2


def test_global_search_filter_controls_are_keyboard_and_touch_friendly():
    assert 'role="group"' in SOURCE
    assert ':aria-pressed="searchFilter === filter"' in SOURCE
    assert "min-height: 34px" in SOURCE
    assert "overflow-x: auto" in SOURCE
