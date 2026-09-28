from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORAGE = ROOT / "time-helper" / "desk" / "src" / "storage" / "indexedDB.ts"


def test_generic_indexeddb_writes_mirror_the_active_key_path():
    source = STORAGE.read_text(encoding="utf-8")
    assert "if (typeof store.keyPath === 'string' && !(store.keyPath in record))" in source
    assert "record[store.keyPath] = key" in source


def test_raw_stores_have_a_local_storage_fallback_and_cleanup_path():
    source = STORAGE.read_text(encoding="utf-8")
    assert "const RAW_STORAGE_PREFIX = `${STORAGE_PREFIX}raw_`" in source
    assert "IndexedDB raw getAll failed" in source
    assert "IndexedDB raw put failed" in source
    assert "rawValueKey(value)" in source
    assert "removeFallbackEntries(storeName)" in source
    assert "RAW_STORAGE_PREFIX}${storeName}_" in source
    assert "localStorage.removeItem(`${STORAGE_PREFIX}${storeName}_${key}`)" in source
