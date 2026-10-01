from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (ROOT / "time-helper" / "desk" / "src" / "guide" / "GuideOverlay.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_guide_close_control_is_explicitly_labeled_in_both_locales():
    assert ":aria-label=\"t('guide.closeLabel')\"" in OVERLAY
    assert ":title=\"t('guide.closeLabel')\"" in OVERLAY
    assert I18N.count("'guide.closeLabel':") == 2
