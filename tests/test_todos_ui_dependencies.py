import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = json.loads((ROOT / "to-dos" / "ui" / "package.json").read_text(encoding="utf-8"))
LOCK = json.loads((ROOT / "to-dos" / "ui" / "package-lock.json").read_text(encoding="utf-8"))


def test_compatibility_ui_does_not_ship_an_unused_tailwind_toolchain():
    assert "tailwindcss" not in PACKAGE["devDependencies"]
    assert "postcss" not in PACKAGE["devDependencies"]
    assert "autoprefixer" not in PACKAGE["devDependencies"]
    assert not (ROOT / "to-dos" / "ui" / "tailwind.config.js").exists()
    assert not (ROOT / "to-dos" / "ui" / "postcss.config.js").exists()
    assert "@tailwind" not in (ROOT / "to-dos" / "ui" / "src" / "styles" / "main.css").read_text(encoding="utf-8")


def test_compatibility_ui_lockfile_matches_the_reduced_toolchain():
    root_package = LOCK["packages"][""]["devDependencies"]
    assert "tailwindcss" not in root_package
    assert "postcss" not in root_package
    assert "autoprefixer" not in root_package
