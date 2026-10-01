from pathlib import Path


BACKUP = Path("time-helper/desk/src/storage/backup.ts").read_text(encoding="utf-8")
ARCHIVE = Path("time-helper/desk/src/services/ArchiveService.ts").read_text(encoding="utf-8")


def test_archive_import_restore_preserves_recovery_sources():
    preservation = "!key.startsWith('efflife_backup_') && !key.startsWith('efflife_emergency_backup_')"
    archive_case = BACKUP[BACKUP.index("case 'archive_import':"):BACKUP.index("case 'config':")]

    assert preservation in archive_case
    assert "localStorage.removeItem(key)" in archive_case


def test_in_process_archive_rollback_preserves_recovery_sources():
    preservation = "!key.startsWith('efflife_backup_') && !key.startsWith('efflife_emergency_backup_')"
    restore_function = ARCHIVE[ARCHIVE.index("async function restoreArchiveRuntimeSnapshot"):ARCHIVE.index("async function restoreOptionalJsonDataset")]

    assert preservation in restore_function
    assert "localStorage.removeItem(key)" in restore_function
