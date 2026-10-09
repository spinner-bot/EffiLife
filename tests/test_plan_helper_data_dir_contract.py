from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = (ROOT / "plan-helper" / "web" / "server.py").read_text(encoding="utf-8")


def test_plan_helper_accepts_unified_data_root_from_environment():
    assert 'data_dir = data_dir or os.environ.get("EFFILIFE_DATA_DIR", "").strip() or None' in SERVER
    assert 'os.environ["EFFILIFE_PLAN_ARCHIVE_DIR"]' in SERVER
    assert 'os.chdir(runtime_dir)' in SERVER

