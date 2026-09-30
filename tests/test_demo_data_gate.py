from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = (ROOT / "time-helper" / "desk" / "src" / "stores" / "app.ts").read_text(encoding="utf-8")


def test_first_launch_demo_data_is_opt_in():
    assert "const ENABLE_SAMPLE_DATA = import.meta.env.VITE_EFFILIFE_DEMO_DATA === 'true'" in STORE
    assert "if (recordsEmpty && ENABLE_SAMPLE_DATA)" in STORE
    assert "if (recordsEmpty) {" not in STORE
