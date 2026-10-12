from pathlib import Path


SOURCE = Path("time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")


def test_recovery_entries_load_before_optional_integrity_probe():
    block = SOURCE.split("async function loadDataStatus", 1)[1].split("async function handleRestoreBackup", 1)[0]
    assert "backupsList.value = getAllBackups()" in block
    assert block.index("backupsList.value = getAllBackups()") < block.index("try {")
    assert block.index("dataStatus.value = status") > block.index("const status = await checkDataIntegrity()")
