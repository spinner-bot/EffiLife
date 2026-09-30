from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper" / "desk" / "src"
I18N = SRC / "i18n" / "index.ts"


def _catalog_keys(source: str, locale: str, next_locale: str | None = None) -> set[str]:
    start = source.index(f"'{locale}': {{")
    end = source.index(f"'{next_locale}': {{", start) if next_locale else source.index("\n  },\n}", start)
    block = source[start:end]
    return set(re.findall(r"^\s*['\"]([^'\"]+)['\"]\s*:", block, re.MULTILINE))


def _literal_translation_keys() -> set[str]:
    keys: set[str] = set()
    call_pattern = re.compile(r"(?<![\w$])(?:t|translate)\(\s*(['\"])([^'\"]+)\1")
    for path in SRC.rglob("*"):
        if path.suffix not in {".vue", ".ts"} or path == I18N:
            continue
        keys.update(match.group(2) for match in call_pattern.finditer(path.read_text(encoding="utf-8")))
    return keys


def test_literal_frontend_translation_keys_exist_in_both_catalogs():
    source = I18N.read_text(encoding="utf-8")
    zh_keys = _catalog_keys(source, "zh-CN", "en-US")
    en_keys = _catalog_keys(source, "en-US")
    used = _literal_translation_keys()

    assert used <= zh_keys, f"missing zh-CN translation keys: {sorted(used - zh_keys)}"
    assert used <= en_keys, f"missing en-US translation keys: {sorted(used - en_keys)}"
