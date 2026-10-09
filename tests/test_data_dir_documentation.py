from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_readme_documents_the_unified_data_dir_contract():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "EFFILIFE_DATA_DIR" in readme
    assert "Plan Helper" in readme
    assert "python plan-helper/web/server.py" in readme
    assert "未设置" in readme

