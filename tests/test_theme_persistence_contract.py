from pathlib import Path


APP_STORE = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")
DATA_SERVICE = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "services" / "dataService.ts").read_text(encoding="utf-8")


def test_config_writes_normalize_rich_theme_at_memory_and_durable_boundaries():
    assert "const normalizedConfig = normalizeConfig(newConfig)" in APP_STORE
    assert "config.value = normalizedConfig" in APP_STORE
    assert "await DataService.saveConfig(normalizedConfig)" in APP_STORE
    assert "const normalized = normalizeConfig(config)" in DATA_SERVICE
    assert "idbSet(STORE_NAMES.CONFIG, 'config', normalized)" in DATA_SERVICE
    assert "JSON.stringify(normalized)" in DATA_SERVICE
