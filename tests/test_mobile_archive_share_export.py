from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_mobile_export_prefers_shareable_archive_file():
    assert "navigator.share" in ARCHIVE
    assert "navigator.canShare({ files: [archiveFile] })" in ARCHIVE
    assert "new File([blob], fileName" in ARCHIVE


def test_mobile_share_cancel_does_not_trigger_fallback_download():
    share_branch = ARCHIVE[ARCHIVE.index("if (isMobilePlatform() && typeof navigator"):ARCHIVE.index("// Mobile Tauri or browser environments")]
    assert "error.name === 'AbortError'" in share_branch
    assert "return { success: false }" in share_branch
    assert "saveAs(blob, fileName)" not in share_branch


def test_mobile_share_title_is_localized():
    assert "'settings.archive.shareTitle':" in I18N
