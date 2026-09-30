from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_notification_and_inbox_icon_buttons_have_localized_names():
    popup = (ROOT / "time-helper" / "desk" / "src" / "audio" / "EventPopup.vue").read_text(encoding="utf-8")
    home = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
    records = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
    events = (ROOT / "time-helper" / "desk" / "src" / "views" / "EventManagerView.vue").read_text(encoding="utf-8")

    assert ":aria-label=\"t('app.closeNotification')\"" in popup
    assert ":aria-label=\"t('home.openInbox')\"" in home
    assert ":aria-label=\"t('home.closeInbox')\"" in home
    assert ":aria-label=\"t('search.close')\"" in records
    for source in (home, events):
        assert 'role="button"' in source
        assert 'tabindex="0"' in source
        assert "@keydown=\"activateInboxEntry" in source


def test_inbox_labels_exist_in_both_locales():
    catalog = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")
    for key in ("home.openInbox", "home.closeInbox"):
        assert catalog.count(f"'{key}'") == 2
