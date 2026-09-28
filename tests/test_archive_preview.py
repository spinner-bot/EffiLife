from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_archive_import_exposes_a_read_only_preview_before_confirmation():
    service = SERVICE.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")
    assert "export async function previewArchive(file: Blob)" in service
    assert "summarizeArchive(await parseArchiveData(zip))" in service
    assert "previewArchive(file)" in settings
    assert "formatArchivePreview(preview)" in settings


def test_archive_preview_translation_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    assert source.count("'settings.archive.importPreview'") == 2


def test_archive_manifest_contains_dataset_checksums_and_import_verifies_them():
    source = SERVICE.read_text(encoding="utf-8")
    assert "async function sha256Hex(bytes: Uint8Array)" in source
    assert "dataset_sha256: datasetSha256" in source
    assert "manifest.dataset_sha256?.[name]" in source
    assert "settings.archive.datasetChecksumMismatch" in source
    assert "'settings.archive.datasetChecksumMismatch'" in I18N.read_text(encoding="utf-8")
