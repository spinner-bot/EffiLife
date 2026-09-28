from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_version_view_uses_catalog_labels_for_build_mode():
    assert "isDev ? t('version.build.development') : t('version.build.release')" in SETTINGS
