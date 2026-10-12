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


def test_collection_and_empty_checks_clear_read_timeouts():
    get_all = INDEXED_DB.split("export async function getAll", 1)[1].split("// 原始对象存储", 1)[0]
    is_empty = INDEXED_DB.split("export async function isEmpty", 1)[1].split("// 关闭数据库", 1)[0]
    for block in (get_all, is_empty):
        assert "const timeout = setTimeout" in block
        assert "clearTimeout(timeout)" in block
        assert "IndexedDB read timed out after" in block
