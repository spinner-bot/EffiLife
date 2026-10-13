from pathlib import Path


SOURCE = Path("time-helper/desk/src/storage/backup.ts").read_text(encoding="utf-8")


def test_normal_backup_restore_broadcasts_supported_workspace_sources():
    assert "notifyWorkspaceChanged, type WorkspaceChangeSource" in SOURCE
    assert "changeSource = 'settings'" in SOURCE
    assert "changeSource = 'plans'" in SOURCE
    assert "changeSource = 'records'" in SOURCE
    assert "if (changeSource) notifyWorkspaceChanged(changeSource)" in SOURCE


def test_unknown_backup_modules_do_not_emit_a_false_workspace_refresh():
    assert "let changeSource: WorkspaceChangeSource | null = null" in SOURCE
    assert "Unknown/legacy backup modules remain silent" in SOURCE


def test_backup_module_discovery_preserves_module_names_with_underscores():
    assert "backup.module === 'string'" in SOURCE
    assert "rest.lastIndexOf('_')" in SOURCE
    assert "rest.split('_')[0]" not in SOURCE


def test_backup_readers_validate_record_shape_before_exposing_recovery_entries():
    assert "function parseBackupRecord" in SOURCE
    assert "typeof candidate.module !== 'string'" in SOURCE
    assert "Number.isNaN(new Date(candidate.timestamp).getTime())" in SOURCE
    assert "if (!('data' in candidate)) return null" in SOURCE
    assert SOURCE.count("parseBackupRecord(JSON.parse(localStorage.getItem(key) || '{}'))") == 3


def test_backup_readers_hide_empty_historical_migration_checkpoints():
    assert "function isRestorableBackup(backup: BackupData): boolean" in SOURCE
    assert "backup.module !== 'pre_migration_full'" in SOURCE
    assert "EMPTY_MIGRATION_METADATA_KEYS" in SOURCE
    assert "backup && isRestorableBackup(backup)" in SOURCE


def test_backup_module_discovery_does_not_expose_malformed_json_as_an_empty_module():
    assert "// A malformed record must not create an empty recovery module." in SOURCE
    assert "continue\n      }\n      const rest = key.slice(prefix.length)" in SOURCE


def test_backup_keys_keep_millisecond_precision_and_delete_legacy_second_keys():
    assert "function formatBackupTimestamp(timestamp: string): string" in SOURCE
    assert "const timestamp = new Date().toISOString()" in SOURCE
    assert "formatBackupTimestamp(timestamp)" in SOURCE
    assert "function removeLocalStorageBackup(moduleName: string, timestamp: string): void" in SOURCE
    assert "formatLegacyBackupTimestamp(timestamp)" in SOURCE
