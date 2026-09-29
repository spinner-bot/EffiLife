from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_starts_with_animated_product_cover():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    first_line = next(line.strip() for line in readme.splitlines() if line.strip())

    assert first_line.startswith('<img src="assets/hero.svg"')
    assert "prefers-reduced-motion" in (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")
    assert "### 三步工作流" in readme
    assert "记录 Capture" in readme
    assert "组织 Organize" in readme
    assert "推进 Focus" in readme


def test_hero_svg_has_accessible_metadata():
    hero = (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")

    assert '<title id="heroTitle">' in hero
    assert '<desc id="heroDesc">' in hero


def test_readme_keeps_current_product_boundaries():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "launcher 仅用于开发、测试、迁移与回归" in readme
    assert "正式用户应使用 Tauri 安装包" in readme
    assert "日历视图" not in readme
