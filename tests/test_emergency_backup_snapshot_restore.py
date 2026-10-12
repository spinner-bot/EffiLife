from pathlib import Path


SOURCE = Path("time-helper/desk/src/storage/recovery.ts").read_text(encoding="utf-8")


def test_emergency_restore_replaces_runtime_local_storage_without_removing_backups():
    clear_stale_keys = "key.startsWith('efflife_') && !key.startsWith('efflife_emergency_backup_')"
    restore_block = SOURCE[SOURCE.index("// 恢复 localStorage 数据"):]

    assert clear_stale_keys in restore_block
    assert "localStorage.removeItem(key)" in restore_block
    assert restore_block.index("localStorage.removeItem(key)") < restore_block.index("for (const [key, value] of Object.entries(data.localStorage))")


def test_emergency_restore_captures_complete_snapshot_and_reports_rollback_outcome():
    assert "function isCompleteEmergencySnapshot" in SOURCE
    assert "const candidate = await exportEmergencyBackup()" in SOURCE
    assert "if (isCompleteEmergencySnapshot(parsed)) rollbackJson = candidate" in SOURCE
    assert "settings.restore.restoreRolledBack" in SOURCE
    assert "settings.restore.restoreRollbackFailed" in SOURCE
    assert "settings.restore.restoreRolledBack" in Path("time-helper/desk/src/i18n/index.ts").read_text(encoding="utf-8")
