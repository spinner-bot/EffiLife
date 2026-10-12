from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORAGE = ROOT / "time-helper" / "desk" / "src" / "storage" / "indexedDB.ts"


def test_indexeddb_set_resolves_after_transaction_commit_not_request_success():
    source = STORAGE.read_text(encoding="utf-8")
    set_block = source.split("export async function set", 1)[1].split("// 通用 DELETE", 1)[0]
    assert "transaction.oncomplete" in set_block
    assert "transaction.onerror" in set_block
    assert "transaction.onabort" in set_block
    assert "request.onsuccess" not in set_block
    assert set_block.index("transaction.oncomplete") < set_block.index("resolve()")


def test_raw_writes_wait_for_transaction_commit_before_resolving():
    source = STORAGE.read_text(encoding="utf-8")
    for function_name in ("putRaw", "deleteRaw"):
        block = source.split(f"export async function {function_name}", 1)[1]
        block = block.split("export async function", 1)[0]
        assert "transaction.oncomplete" in block
        assert "transaction.onerror" in block
        assert "transaction.onabort" in block
        assert "request.onsuccess" not in block


def test_generic_delete_cleans_fallback_only_after_transaction_commit():
    source = STORAGE.read_text(encoding="utf-8")
    block = source.split("export async function del", 1)[1].split("// 获取存储中的所有数据", 1)[0]
    assert "transaction.oncomplete" in block
    assert "transaction.onerror" in block
    assert "transaction.onabort" in block
    assert "request.onsuccess" not in block
    assert block.index("transaction.oncomplete") < block.index("localStorage.removeItem")


def test_clear_waits_for_transaction_commit_before_removing_fallback_mirrors():
    source = STORAGE.read_text(encoding="utf-8")
    block = source.split("export async function clear", 1)[1].split("export async function isEmpty", 1)[0]
    assert "transaction.oncomplete" in block
    assert "transaction.onerror" in block
    assert "transaction.onabort" in block
    assert block.index("transaction.oncomplete") < block.index("removeFallbackEntries(storeName)")
