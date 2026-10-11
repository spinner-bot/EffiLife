import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESK = ROOT / "time-helper" / "desk"


def load_package_json():
    return json.loads((DESK / "package.json").read_text(encoding="utf-8"))


def test_desktop_does_not_carry_unused_tailwind_postcss_or_lint_toolchain():
    package = load_package_json()
    dev_dependencies = package.get("devDependencies", {})
    forbidden = {"tailwindcss", "postcss", "autoprefixer", "eslint", "eslint-plugin-vue", "@vue/eslint-config-typescript"}
    assert forbidden.isdisjoint(dev_dependencies)
    assert not (DESK / "postcss.config.js").exists()
    assert not (DESK / "tailwind.config.js").exists()
    css = (DESK / "src" / "styles" / "main.css").read_text(encoding="utf-8")
    assert "@tailwind" not in css


def test_desktop_dependency_overrides_pin_audited_transitive_fixes():
    package = load_package_json()
    assert package["overrides"] == {
        "brace-expansion": "2.1.7",
        "source-map-js": "1.2.2",
    }
