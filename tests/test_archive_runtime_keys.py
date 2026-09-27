from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_legacy_keys_match_runtime_services():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "DAILY_TRIGGER: 'efflife_daily_triggers'" in source
    assert "CHECKIN: 'efflife_checkin_data'" in source
