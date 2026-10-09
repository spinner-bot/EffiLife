from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "build_frontend.py").read_text(encoding="utf-8")


def test_frontend_build_entrypoint_reuses_launcher_toolchain_resolution():
    assert "start.find_npm()" in SCRIPT
    assert "start.node_environment()" in SCRIPT
    assert '"run", "build"' in SCRIPT
    assert "cwd=DESK" in SCRIPT


def test_frontend_build_entrypoint_has_actionable_missing_node_message():
    assert "EFFILIFE_NODE_DIR" in SCRIPT
    assert "install Node.js on PATH" in SCRIPT
