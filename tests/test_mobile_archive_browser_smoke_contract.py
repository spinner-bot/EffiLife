from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "smoke_browser_workspace.py").read_text(encoding="utf-8")


def test_browser_smoke_exposes_mobile_archive_share_flow():
    assert '"--mobile-archive-share-flow"' in SCRIPT
    assert "mobile_archive_share_verified" in SCRIPT
    assert "__efflifeSharedArchive" in SCRIPT
    assert "mobile archive export did not enter the system share path" in SCRIPT

