from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def version(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").strip()


def test_readme_module_versions_match_version_files():
    assert f"| time-helper | {version('time-helper/VERSION')} |" in README
    assert f"| plan-helper | {version('plan-helper/VERSION')} |" in README
    assert f"| to-dos | {version('to-dos/VERSION')} |" in README


def test_readme_describes_current_mobile_scope():
    assert "Android 真机验收待完成；iOS 按当前范围暂缓" in README
