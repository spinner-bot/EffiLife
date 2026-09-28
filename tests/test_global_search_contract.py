from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue").read_text(encoding="utf-8")


def test_global_search_uses_unwrapped_record_reader():
    assert "import { getAll, STORE_NAMES } from '@/storage'" in SOURCE
    assert "getAll<TimeRecord[]>(STORE_NAMES.RECORDS)" in SOURCE
    assert "getRawAll<TimeRecord[]>(STORE_NAMES.RECORDS)" not in SOURCE
