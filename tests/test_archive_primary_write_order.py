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
