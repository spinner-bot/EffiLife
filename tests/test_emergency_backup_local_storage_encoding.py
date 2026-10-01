from pathlib import Path


SOURCE = Path("time-helper/desk/src/storage/recovery.ts").read_text(encoding="utf-8")


def test_emergency_backup_preserves_raw_local_storage_values_with_versioned_encoding():
    assert "backupData.localStorageEncoding = 'raw-v2'" in SOURCE
    assert "localStorageData[key] = localStorage.getItem(key) || ''" in SOURCE
    assert "data.localStorageEncoding === 'raw-v2' && typeof value === 'string'" in SOURCE


def test_legacy_emergency_backups_keep_the_json_stringify_restore_path():
    restore_expression = "data.localStorageEncoding === 'raw-v2' && typeof value === 'string'"
    assert restore_expression in SOURCE
    assert "JSON.stringify(value)" in SOURCE
