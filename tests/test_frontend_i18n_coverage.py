import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper" / "desk" / "src"
CATALOG = SRC / "i18n" / "index.ts"


def test_all_static_frontend_translation_calls_exist_in_both_locales():
    catalog = CATALOG.read_text(encoding="utf-8")
    used = set()
    for path in SRC.rglob("*"):
        if path.suffix not in {".ts", ".vue"} or path == CATALOG:
            continue
        used.update(re.findall(r"(?:\bt|\btranslate)\(\s*['\"]([^'\"]+)['\"]", path.read_text(encoding="utf-8")))

    missing = sorted(key for key in used if catalog.count(f"'{key}'") < 2)
    assert not missing, f"missing bilingual frontend translation keys: {missing}"
