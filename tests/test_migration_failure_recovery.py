from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts"


def test_migration_failure_blocks_workspace_hydration_instead_of_falling_back_silently():
    source = DATA_SERVICE.read_text(encoding="utf-8")
    block = source.split("async function ensureMigration(): Promise<void>", 1)[1].split("// 触发备份", 1)[0]
    assert "if (!result.success)" in block
    assert "throw new Error(`Data migration failed: ${result.errors.join('; ')}`)" in block


def test_migration_retry_discards_rejected_promise_for_startup_retry():
    source = DATA_SERVICE.read_text(encoding="utf-8")
    block = source.split("async function ensureMigration(): Promise<void>", 1)[1].split("// 触发备份", 1)[0]
    assert "migrationPromise = null" in block
    assert "throw error" in block
    assert "migrationPromise = runMigration()" in block


def test_migration_does_not_write_any_dataset_when_pre_migration_backup_fails():
    source = (ROOT / "time-helper/desk/src/storage/migration.ts").read_text(encoding="utf-8")
    migration = source.split("export async function runMigration", 1)[1]
    backup_block = migration.split("// 执行各项迁移", 1)[0]
    assert "return {" in backup_block
    assert "success: false" in backup_block
    assert "errors: [failure]" in backup_block
    assert migration.index("errors: [failure]") < migration.index("const migrations:")


def test_local_storage_integrity_ignores_backup_and_runtime_metadata_keys():
    source = (ROOT / "time-helper/desk/src/storage/migration.ts").read_text(encoding="utf-8")
    assert "function isWorkspaceDataStorageKey(key: string): boolean" in source
    assert "'efflife_backup_'" in source
    assert "'efflife_emergency_backup_'" in source
    assert "'efflife_workspace_event'" in source
    assert "if (key && isWorkspaceDataStorageKey(key))" in source
