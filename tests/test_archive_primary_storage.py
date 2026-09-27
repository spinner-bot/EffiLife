import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_collects_core_data_from_indexeddb_before_legacy_mirror():
    source = ARCHIVE.read_text(encoding="utf-8")

    assert "async function readCoreJSON" in source
    assert "await get<T>(storeName, storeKey)" in source
    collect = source.split("async function collectAllData", 1)[1].split("export async function exportArchive", 1)[0]
    for key in ("config", "plans", "scheduleRules", "manualPlans"):
        assert re.search(rf"{key}: await readCoreJSON", collect)
