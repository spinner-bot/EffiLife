from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = (ROOT / "time-helper/desk/src/views/SettingsView.vue").read_text(encoding="utf-8")


def test_rich_theme_controls_have_native_label_associations():
    control_ids = (
        "theme-solid-bg-window",
        "theme-solid-bg-button",
        "theme-solid-fg-button",
        "theme-gradient-start",
        "theme-gradient-end",
        "theme-gradient-direction",
        "theme-glass-background",
        "theme-glass-opacity",
        "theme-glass-blur",
        "theme-neon-background",
        "theme-neon-color",
        "theme-neon-accent",
        "theme-neon-glow",
    )
    for control_id in control_ids:
        assert f'for="{control_id}"' in SETTINGS
        assert f'id="{control_id}"' in SETTINGS
