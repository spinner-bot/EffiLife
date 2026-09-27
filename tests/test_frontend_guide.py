import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUIDE_SOURCE = ROOT / "time-helper" / "desk" / "src" / "guide" / "GuideManager.ts"
OVERLAY_SOURCE = ROOT / "time-helper" / "desk" / "src" / "guide" / "GuideOverlay.vue"
I18N_SOURCE = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_onboarding_targets_unified_navigation():
    source = GUIDE_SOURCE.read_text(encoding="utf-8")
    current_steps = source.split("MAIN_GUIDE.steps = [", 1)[1].split("\n]", 1)[0]

    assert ".global-nav-link:nth-child(2)" in current_steps
    assert ".global-nav-link:nth-child(3)" in current_steps
    assert ".global-nav-link:nth-child(4)" in current_steps
    assert ".global-nav-link:nth-child(5)" in current_steps
    assert ".pv-tab" not in current_steps
    assert ".nav-btn" not in current_steps


def test_onboarding_copy_is_localized_in_both_catalogs():
    guide = GUIDE_SOURCE.read_text(encoding="utf-8")
    overlay = OVERLAY_SOURCE.read_text(encoding="utf-8")
    catalog = I18N_SOURCE.read_text(encoding="utf-8")
    keys = set(re.findall(r"(?:titleKey|descriptionKey): '([^']+)'", guide))
    keys.update(re.findall(r"t\('([^']+)'\)", overlay))

    for key in keys:
        assert re.search(rf"'{re.escape(key)}':", catalog), f"missing guide i18n key: {key}"

