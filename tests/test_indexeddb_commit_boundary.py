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
