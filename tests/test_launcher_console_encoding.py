from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "launcher" / "start.py").read_text(encoding="utf-8")


def test_launcher_configures_utf8_console_output_without_breaking_embedded_hosts():
    assert "def configure_console_encoding() -> None:" in SOURCE
    assert "reconfigure(encoding=\"utf-8\", errors=\"replace\")" in SOURCE
    assert "except (OSError, ValueError):" in SOURCE
    assert "configure_console_encoding()" in SOURCE
