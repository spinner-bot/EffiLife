from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_compatibility_mirror_is_best_effort():
    source = ARCHIVE.read_text(encoding="utf-8")
    write_block = source.split("function writeJSON", 1)[1].split("// Core data", 1)[0]
    assert "try {" in write_block
    assert "localStorage.setItem(key, JSON.stringify(data))" in write_block
    assert "console.warn(`Failed to update archive compatibility mirror" in write_block


def test_optional_archive_restore_commits_primary_store_before_legacy_mirror():
    source = ARCHIVE.read_text(encoding="utf-8")
    block = source.split("async function restoreOptionalJsonDataset", 1)[1].split("async function processArchiveData", 1)[0]
    assert block.index("await idbSet(storeName, storeKey, value)") < block.index("writeJSON(localKey, value)")
    assert block.index("await idbClear(storeName)") < block.index("localStorage.removeItem(localKey)")


def test_archive_checkpoint_and_rollback_tolerate_unavailable_legacy_storage():
    source = ARCHIVE.read_text(encoding="utf-8")
    capture = source.split("async function captureArchiveRuntimeSnapshot", 1)[1].split("async function restoreArchiveRuntimeSnapshot", 1)[0]
    restore = source.split("async function restoreArchiveRuntimeSnapshot", 1)[1].split("async function restoreOptionalJsonDataset", 1)[0]
    assert "try {" in capture
    assert "IndexedDB remains sufficient for the canonical rollback snapshot" in capture
    assert "try {" in restore
    assert "Do not hide or undo the canonical IndexedDB rollback" in restore
