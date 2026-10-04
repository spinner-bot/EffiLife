from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_version_management_spec_matches_module_version_files():
    spec = (ROOT / "docs/spec/版本管理规范.txt").read_text(encoding="utf-8")
    expected = {
        "time-helper/VERSION": (ROOT / "time-helper/VERSION").read_text(encoding="utf-8").strip(),
        "plan-helper/VERSION": (ROOT / "plan-helper/VERSION").read_text(encoding="utf-8").strip(),
        "to-dos/VERSION": (ROOT / "to-dos/VERSION").read_text(encoding="utf-8").strip(),
    }
    for path, version in expected.items():
        assert f"`{path}` — 当前 {version}" in spec
        module = path.removesuffix("/VERSION")
        assert f"`{module}/v{version}`" in spec


def test_version_management_spec_keeps_no_stale_current_versions():
    spec = (ROOT / "docs/spec/版本管理规范.txt").read_text(encoding="utf-8")
    assert "当前 1.0.15" not in spec
    assert "当前 0.2.0" not in spec
    assert "当前 0.1.0" not in spec
