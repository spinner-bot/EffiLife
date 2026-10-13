from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IGNORE = ROOT / "plan-helper" / ".gitignore"


def test_plan_helper_ignores_standalone_runtime_state_but_keeps_fixture_directories():
    source = IGNORE.read_text(encoding="utf-8")
    assert "data/archives/*.json" in source
    assert "data/system/registry/*.json" in source
    assert "keep .gitkeep" in source
