from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_starts_with_animated_product_cover():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    first_line = next(line.strip() for line in readme.splitlines() if line.strip())

    assert first_line.startswith('<img src="assets/hero.svg"')
    assert "prefers-reduced-motion" in (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")


def test_hero_svg_has_accessible_metadata():
    hero = (ROOT / "assets" / "hero.svg").read_text(encoding="utf-8")

    assert '<title id="heroTitle">' in hero
    assert '<desc id="heroDesc">' in hero
