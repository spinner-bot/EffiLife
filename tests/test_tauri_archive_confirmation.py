from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"
SETTINGS = ROOT / "time-helper" / "desk" / "src" / "views" / "SettingsView.vue"


def test_tauri_import_confirms_after_reading_archive_before_processing():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "importArchiveWithDialog(confirmImport?: () => boolean)" in source
    assert "if (confirmImport && !confirmImport())" in source
    assert "return { success: false, message: '', cancelled: true }" in source
    assert source.index("if (confirmImport && !confirmImport())") < source.index("return await processArchiveData(zip)", source.index("if (confirmImport && !confirmImport())"))


def test_archive_import_accepts_case_insensitive_efl_extension():
    source = (ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")
    assert "file.name.toLocaleLowerCase().endsWith('.efl')" in source


def test_settings_passes_the_existing_overwrite_confirmation_to_tauri_import():
    source = SETTINGS.read_text(encoding="utf-8")
    assert "importArchiveWithDialog(() => confirm(t('settings.archive.importConfirm')))" in source
