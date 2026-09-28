from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_reset_data_notifies_other_workspace_windows_before_reload():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "const changeSource = type === 'all'" in source
    assert "? 'archive'" in source
    assert "? 'records'" in source
    assert "? 'plans'" in source
    assert ": 'settings'" in source
    assert "notifyWorkspaceChanged(changeSource)" in source
    assert source.index("notifyWorkspaceChanged(changeSource)") < source.index("window.location.reload()")

