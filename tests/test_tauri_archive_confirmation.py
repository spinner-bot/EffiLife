from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_tauri_import_confirms_after_reading_archive_before_processing():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "importArchiveWithDialog(confirmImport?: (preview: ArchivePreview) => boolean | Promise<boolean>)" in source
    assert "const preview = await addLocalArchiveScope(summarizeArchive(await parseArchiveData(zip)))" in source
    assert "if (confirmImport && !(await confirmImport(preview)))" in source
    assert "return { success: false, message: '', cancelled: true }" in source
    confirmation = "if (confirmImport && !(await confirmImport(preview)))"
    assert source.index("const preview = await addLocalArchiveScope(summarizeArchive(await parseArchiveData(zip)))") < source.index(confirmation)
    assert source.index(confirmation) < source.index("return await processArchiveData(zip)", source.index(confirmation))


def test_archive_import_accepts_case_insensitive_efl_extension():
    source = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    assert "file.name.toLocaleLowerCase().endsWith('.efl')" in source


def test_settings_passes_the_existing_overwrite_confirmation_to_tauri_import():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "importArchiveWithDialog((preview) => requestConfirm(`${formatArchivePreview(preview)}\\n\\n${t('settings.archive.importConfirm')}`, { tone: 'danger' }))" in source
