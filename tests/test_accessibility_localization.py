from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ICON_PREVIEW = ROOT / "time-helper" / "desk" / "src" / "components" / "CategoryIconPreview.vue"
CHECKIN = ROOT / "time-helper" / "desk" / "src" / "views" / "CheckinView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_category_icon_fallback_uses_localized_accessible_name():
    source = ICON_PREVIEW.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    assert "useI18n" in source
    assert "t('tasks.categoryIcon')" in source
    assert "|| 'category'" not in source
    assert catalog.count("'tasks.categoryIcon':") == 2


def test_checkin_heatmap_exposes_a_localized_title():
    source = CHECKIN.read_text(encoding="utf-8")
    assert ':title="t(\'checkin.heatmap\')"' in source
    assert 'title=""' not in source
