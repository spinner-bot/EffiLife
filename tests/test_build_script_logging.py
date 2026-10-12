from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_build_scripts_flush_context_before_child_process_output():
    for name in ("build_frontend.py", "build_todos_ui.py"):
        source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert 'print(f"Building ' in source
        assert 'flush=True' in source
