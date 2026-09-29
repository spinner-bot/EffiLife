from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_uses_authoritative_desktop_version():
    version = (ROOT / "time-helper" / "VERSION").read_text(encoding="utf-8").strip()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"| time-helper | {version} |" in readme


def test_readme_exposes_animated_product_cover():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    hero = (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")

    assert '<img src="assets/hero.svg"' in readme
    assert 'alt="EffiLife' in readme
    assert '<title id="heroTitle">EffiLife' in hero
    assert "@keyframes spin" in hero
    assert "@keyframes flow" in hero
    assert "prefers-reduced-motion: reduce" in hero


def test_animated_cover_describes_the_unified_product_domains():
    hero = (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")

    for label in ("时间记录", "计划编排", "待办协同"):
        assert label in hero
    assert "Unified Personal Time Management" in hero
