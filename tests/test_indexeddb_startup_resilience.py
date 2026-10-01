from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEXED_DB = (ROOT / "time-helper" / "desk" / "src" / "storage" / "indexedDB.ts").read_text(encoding="utf-8")


def test_indexeddb_open_has_a_bounded_fallback_path():
    assert "const DB_OPEN_TIMEOUT_MS = 3000" in INDEXED_DB
    assert "setTimeout(() =>" in INDEXED_DB
    assert "IndexedDB open timed out after" in INDEXED_DB
    assert "dbPromise = null" in INDEXED_DB
    assert "clearTimeout(timeout)" in INDEXED_DB


def test_indexeddb_reads_have_a_bounded_fallback_path():
    assert "const DB_READ_TIMEOUT_MS = 3000" in INDEXED_DB
    assert "IndexedDB read timed out after" in INDEXED_DB
    assert "IndexedDB raw read timed out after" in INDEXED_DB
