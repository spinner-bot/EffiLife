from pathlib import Path


ROUTER = Path("time-helper/desk/src/router/index.ts").read_text(encoding="utf-8")
VIEW = Path("time-helper/desk/src/views/NotFoundView.vue").read_text(encoding="utf-8")
I18N = Path("time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")


def test_router_has_a_localized_fallback_page():
    assert "path: '/:pathMatch(.*)*'" in ROUTER
    assert "NotFoundView.vue" in ROUTER
    assert "t('notFound.title')" in VIEW
    assert "to=\"/\"" in VIEW


def test_not_found_copy_exists_in_both_locales():
    assert I18N.count("'notFound.title'") == 2
    assert I18N.count("'notFound.description'") == 2
    assert I18N.count("'notFound.backHome'") == 2
