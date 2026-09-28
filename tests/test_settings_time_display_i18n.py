from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_time_display_options_use_translation_keys():
    source = SETTINGS.read_text(encoding="utf-8")
    for key in ("settings.showSeconds", "settings.use24h", "settings.showAmPm"):
        assert f"t('{key}')" in source
    assert "<span>显示秒</span>" not in source
    assert "<span>24小时制</span>" not in source
    assert "<span>半日显示(AM/PM)</span>" not in source


def test_time_display_translation_keys_exist_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("settings.showSeconds", "settings.use24h", "settings.showAmPm"):
        assert source.count(f"'{key}'") == 2
