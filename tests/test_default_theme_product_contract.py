from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_SERVICE = (ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts").read_text(encoding="utf-8")
THEME_ENGINE = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")


def test_new_users_start_with_system_adaptive_theme():
    config_start = DATA_SERVICE.index("export const DEFAULT_CONFIG")
    theme_start = DATA_SERVICE.index("theme:", config_start)
    solid_start = DATA_SERVICE.index("solid:", theme_start)
    assert "type: 'system'" in DATA_SERVICE[theme_start:solid_start]


def test_unhydrated_theme_engine_fallback_is_readable_system_theme():
    fallback = THEME_ENGINE.split("if (!theme)", 1)[1].split("const preset", 1)[0]
    assert "theme = { type: 'system' }" in fallback
