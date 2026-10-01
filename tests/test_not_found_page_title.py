from pathlib import Path


SOURCE = Path("time-helper/desk/src/App.vue").read_text(encoding="utf-8")


def test_not_found_route_has_a_localized_document_title():
    assert "if (route.name === 'notFound') return t('notFound.title')" in SOURCE
    assert "document.title = t('app.documentTitle', { page: pageTitle.value })" in SOURCE
