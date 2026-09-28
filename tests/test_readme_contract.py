from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_uses_authoritative_desktop_version():
    version = (ROOT / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"| time-helper | {version} |" in readme
