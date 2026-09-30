from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue").read_text(encoding="utf-8")


def test_settings_statistics_load_cannot_block_page_initialization():
    mounted_block = SETTINGS.split("onMounted(async () =>", 1)[1].split("// 检查数据完整性", 1)[0]
    assert "try {" in mounted_block
    assert "dataStats.value = await getDataStats()" in mounted_block
    assert "Failed to load settings data statistics:" in mounted_block
    assert "isLoading.value = false" in mounted_block

