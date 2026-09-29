from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = (ROOT / "time-helper" / "desk" / "src" / "theme" / "ThemeEngine.ts").read_text(encoding="utf-8")


def test_theme_tokens_expose_native_control_color_scheme():
    assert "'color-scheme': getColorScheme(style.bgColor)" in ENGINE
    assert "function getColorScheme(color: string): 'dark' | 'light'" in ENGINE
    assert "return getLuminance(normalized) < 128 ? 'dark' : 'light'" in ENGINE


def test_theme_color_scheme_safely_falls_back_for_custom_colors():
    assert "if (!/^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i.test(normalized)) return 'light'" in ENGINE

