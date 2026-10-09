from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH = (ROOT / "time-helper/desk/src/components/GlobalSearch.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_global_search_input_has_a_visible_native_label():
    assert '<label class="search-input-label" for="global-search-input">{{ t(\'search.inputLabel\') }}</label>' in SEARCH
    assert 'id="global-search-input"' in SEARCH
    assert I18N.count("'search.inputLabel':") == 2
