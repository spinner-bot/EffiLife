from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")


def test_config_save_rolls_back_in_memory_state_when_persistence_fails():
    save_block = STORE.split("async function saveConfig", 1)[1].split("// 仅更新运行时配置", 1)[0]
    assert "const previousConfig = config.value" in save_block
    assert "try {" in save_block
    assert "await DataService.saveConfig(newConfig)" in save_block
    assert "config.value = previousConfig" in save_block
    assert "throw error" in save_block

