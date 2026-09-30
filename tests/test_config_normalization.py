from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_SERVICE = (ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts").read_text(encoding="utf-8")


def test_config_reads_use_one_deep_theme_normalizer():
    assert "export function normalizeConfig(stored: Partial<Config>): Config" in DATA_SERVICE
    assert "solid: { ...DEFAULT_CONFIG.theme.solid, ...storedTheme.solid }" in DATA_SERVICE
    assert "gradient: { ...DEFAULT_CONFIG.theme.gradient, ...storedTheme.gradient }" in DATA_SERVICE
    assert "glass: { ...DEFAULT_CONFIG.theme.glass, ...storedTheme.glass }" in DATA_SERVICE
    assert "neon: { ...DEFAULT_CONFIG.theme.neon, ...storedTheme.neon }" in DATA_SERVICE
    assert DATA_SERVICE.count("return normalizeConfig(") == 2
