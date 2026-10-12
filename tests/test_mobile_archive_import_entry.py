from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_archive_import_uses_native_picker_only_on_desktop_tauri():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "if (isTauriRuntime() && !isMobilePlatform())" in source
    assert "importArchiveWithDialog" in source
    assert "fileInputRef.value.click()" in source


def test_mobile_archive_import_does_not_call_desktop_picker_only_branch():
    source = SETTINGS.read_text(encoding="utf-8")
    branch = source[source.index("async function handleImportArchive()"):source.index("async function onFileSelected")]
    assert "isTauriRuntime() && !isMobilePlatform()" in branch
    assert "else {" in branch
    assert "fileInputRef.value.click()" in branch


def test_browser_archive_import_always_releases_busy_state_after_preview_or_confirmation_errors():
    source = SETTINGS.read_text(encoding="utf-8")
    branch = source[source.index("async function onFileSelected"):source.index("// ============ 数据恢复")]
    assert "try {" in branch
    assert "preview = await previewArchive(file)" in branch
    assert "await requestConfirm(`${formatArchivePreview(preview)}\\n\\n${t('settings.archive.importConfirm')}`" in branch
    assert "finally {" in branch
    assert "archiveBusy.value = false" in branch
