import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "time-helper/desk/src"
CATALOG = (SRC / "i18n/index.ts").read_text(encoding="utf-8")


def literal_translation_keys() -> set[str]:
    keys: set[str] = set()
    for path in SRC.rglob("*"):
        if path.suffix not in {".ts", ".vue"} or path.name == "index.ts":
            continue
        source = path.read_text(encoding="utf-8")
        keys.update(re.findall(r"(?:\bt|\btranslate)\(\s*'([^']+)'", source))
    return keys


def test_literal_translation_calls_exist_in_both_locale_catalogs():
    keys = literal_translation_keys()
    assert keys
    missing = {
        key: CATALOG.count(f"'{key}':")
        for key in keys
        if CATALOG.count(f"'{key}':") < 2
    }
    assert missing == {}


def test_known_dynamic_translation_families_exist_in_both_locale_catalogs():
    families = {
        "tasks.iconTab": ("icons", "ascii", "colors"),
        "search.filter": ("all", "th", "ph", "td"),
        "plans.statusFilter": ("all", "active", "completed"),
        "settings.archive.planSource": ("live", "cache", "snapshot", "unavailable"),
    }
    dynamic_keys = [f"{prefix}.{suffix}" for prefix, suffixes in families.items() for suffix in suffixes]
    dynamic_keys.extend(
        f"api.error.{key}"
        for key in re.findall(r"apiFail\('([^']+)'\)", (SRC / "api/index.ts").read_text(encoding="utf-8"))
    )
    assert dynamic_keys
    assert all(CATALOG.count(f"'{key}':") == 2 for key in dynamic_keys)
