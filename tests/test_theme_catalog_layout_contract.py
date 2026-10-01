from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_theme_catalog_uses_semantic_categories_and_counts():
    assert 'class="form-section theme-category"' in SETTINGS
    assert 'role="group"' in SETTINGS
    assert ':aria-labelledby="`theme-category-${category}`"' in SETTINGS
    assert ':id="`theme-category-${category}`"' in SETTINGS
    assert 'availableThemes.filter(theme => themeCategory(theme) === category).length' in SETTINGS


def test_theme_catalog_is_wide_on_desktop_and_collapses_on_small_screens():
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr));' in SETTINGS
    assert '.theme-card:focus-visible' in SETTINGS
    assert '@media (max-width: 680px)' in SETTINGS
    assert '.theme-list { grid-template-columns: 1fr; }' in SETTINGS
