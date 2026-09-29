from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"
BACKUP = ROOT / "time-helper" / "desk" / "src" / "storage" / "backup.ts"


def test_archive_import_persists_checkpoint_before_mutation():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "createBackup('archive_import', runtimeSnapshot)" in source
    assert "Failed to persist archive import checkpoint" in source


def test_archive_import_checkpoint_restores_both_storage_layers():
    source = BACKUP.read_text(encoding="utf-8")
    assert "case 'archive_import'" in source
    assert "localStorage.removeItem(key)" in source
    assert "await clear(storeName)" in source
    assert "await putRaw(storeName, entry)" in source
    assert "changeSource = 'archive'" in source
