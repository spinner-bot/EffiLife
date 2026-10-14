from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "time-helper" / "desk" / "src" / "storage" / "migration.ts"


def test_storage_migration_marker_is_versioned_and_keeps_boolean_compatibility():
    source = MIGRATION.read_text(encoding="utf-8")
    assert "CURRENT_STORAGE_MIGRATION_VERSION = 1" in source
    assert "if (stored === 'true') return 1" in source
    assert "getStoredMigrationVersion() >= CURRENT_STORAGE_MIGRATION_VERSION" in source
    assert "String(CURRENT_STORAGE_MIGRATION_VERSION)" in source


def test_storage_migration_exposes_the_stored_version_for_upgrade_diagnostics():
    source = MIGRATION.read_text(encoding="utf-8")
    assert "export function getStoredMigrationVersion(): number" in source
    assert "Number.parseInt(stored, 10)" in source
