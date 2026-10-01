from pathlib import Path


ARCHIVE = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts").read_text(encoding="utf-8")


def test_archive_import_and_export_normalize_config_theme_sections():
    assert "import { getTodayDate, normalizeConfig } from '@/services/dataService'" in ARCHIVE
    assert "config: normalizeConfig(await readCoreJSON<Partial<Config>>" in ARCHIVE
    assert "config: app.config ? normalizeConfig(app.config as Partial<Config>) as unknown as Record<string, unknown> : null" in ARCHIVE
