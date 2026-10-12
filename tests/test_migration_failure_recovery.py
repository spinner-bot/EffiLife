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
