from pathlib import Path


SOURCE = Path("time-helper/desk/src/storage/backup.ts").read_text(encoding="utf-8")


def test_normal_backup_restore_broadcasts_supported_workspace_sources():
    assert "notifyWorkspaceChanged, type WorkspaceChangeSource" in SOURCE
    assert "changeSource = 'settings'" in SOURCE
    assert "changeSource = 'plans'" in SOURCE
    assert "changeSource = 'records'" in SOURCE
    assert "if (changeSource) notifyWorkspaceChanged(changeSource)" in SOURCE


def test_unknown_backup_modules_do_not_emit_a_false_workspace_refresh():
    assert "let changeSource: WorkspaceChangeSource | null = null" in SOURCE
    assert "Unknown/legacy backup modules remain silent" in SOURCE
