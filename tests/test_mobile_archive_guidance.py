from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_mobile_archive_page_explains_transfer_interactions():
    assert "v-if=\"isMobilePlatform()\" class=\"archive-capability-note archive-mobile-note\"" in VIEW
    assert "settings.archive.mobileTransferTitle" in VIEW
    assert "settings.archive.mobileTransferDescription" in VIEW


def test_mobile_archive_guidance_is_localized_in_both_supported_locales():
    assert I18N.count("settings.archive.mobileTransferTitle") == 2
    assert I18N.count("settings.archive.mobileTransferDescription") == 2
    assert "系统分享面板" in I18N
    assert "system share sheet" in I18N
