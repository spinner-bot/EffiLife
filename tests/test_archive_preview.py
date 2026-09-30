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
    assert "if (error instanceof Error && error.message === checksumError) throw error" in source
    assert "'settings.archive.datasetChecksumMismatch'" in I18N.read_text(encoding="utf-8")


def test_archive_preview_exposes_integrity_status_to_confirmation():
    source = SERVICE.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")
    assert "integrity: 'verified' | 'legacy'" in source
    assert "archiveIntegrity: hasChecksums ? 'verified' : 'legacy'" in source
    assert "preview.integrity === 'verified'" in settings
    assert "settings.archive.integrityLegacy" in settings


def test_archive_preview_discloses_plan_snapshot_status():
    service = SERVICE.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")
    i18n = I18N.read_text(encoding="utf-8")

    assert "planStatus: 'available' | 'stale' | 'unavailable'" in service
    assert "data.planHelper.stale ? 'stale' : 'available'" in service
    assert "preview.planStatus === 'available'" in settings
    assert "settings.archive.planSnapshotLive" in settings
    assert "settings.archive.planSnapshotStale" in settings
    assert i18n.count("'settings.archive.planSnapshotLive'") == 2
    assert i18n.count("'settings.archive.planSnapshotStale'") == 2


def test_archive_preview_discloses_active_and_archived_plan_counts():
    service = SERVICE.read_text(encoding="utf-8")
    settings = SETTINGS.read_text(encoding="utf-8")
    i18n = I18N.read_text(encoding="utf-8")
    assert "archivedPlanCount: number" in service
    assert "data.planHelper.archives" in service
    assert "archivedPlans: preview.archivedPlanCount" in settings
    assert i18n.count("{archivedPlans}") == 2


def test_archive_import_rejects_partial_canonical_bundles_before_writing():
    source = SERVICE.read_text(encoding="utf-8")
    i18n = I18N.read_text(encoding="utf-8")
    assert "CANONICAL_ARCHIVE_DATASETS" in source
    assert "const missingDatasets = CANONICAL_ARCHIVE_DATASETS.filter" in source
    assert "settings.archive.missingDatasets" in source
    assert i18n.count("'settings.archive.missingDatasets'") == 2


def test_legacy_archive_missing_records_preserves_current_data():
    source = SERVICE.read_text(encoding="utf-8")
    assert "records?: Record<string, unknown[]>" in source
    assert "const legacyRecords = legacy.records === undefined ? undefined" in source
    assert "records: legacyRecords" in source
    assert "if (data.records)" in source


def test_frontend_rejects_invalid_canonical_dataset_shapes():
    source = SERVICE.read_text(encoding="utf-8")
    assert "function isObjectRecord(value: unknown)" in source
    assert "datasetInvalid', { name: 'app' }" in source
    assert "datasetInvalid', { name: 'todos' }" in source
    assert "datasetInvalid', { name: 'todo_categories' }" in source
    assert "datasetInvalid', { name: 'records' }" in source
    assert "datasetInvalid', { name: 'plan_helper' }" in source
