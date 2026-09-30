from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_workflows_use_current_node_runtime_actions():
    for name in (
        "tauri-desktop-release.yml",
        "tauri-mobile-build.yml",
        "tauri-mobile-boundary.yml",
    ):
        source = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
        assert "actions/checkout@v4" not in source
        assert "actions/setup-node@v4" not in source
        assert "actions/setup-python@v5" not in source
