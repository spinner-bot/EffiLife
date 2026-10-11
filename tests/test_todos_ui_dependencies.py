import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = json.loads((ROOT / "to-dos" / "ui" / "package.json").read_text(encoding="utf-8"))
LOCK = json.loads((ROOT / "to-dos" / "ui" / "package-lock.json").read_text(encoding="utf-8"))


def test_compatibility_ui_pins_safe_source_map_runtime():
    assert PACKAGE["overrides"]["source-map-js"] == "^1.2.2"
    assert LOCK["packages"]["node_modules/source-map-js"]["version"] == "1.2.2"


def test_compatibility_ui_keeps_tailwind_major_version_explicitly_unchanged():
    # Tailwind 4 is a separate migration and must not be pulled in by an
    # automatic audit fix until the compatibility UI has been migrated.
    assert PACKAGE["devDependencies"]["tailwindcss"].startswith("^3.")
