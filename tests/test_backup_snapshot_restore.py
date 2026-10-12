from pathlib import Path


SOURCE = Path("time-helper/desk/src/storage/backup.ts").read_text(encoding="utf-8")


def test_records_backup_restore_replaces_the_existing_snapshot():
    clear = "await clear(STORE_NAMES.RECORDS)"
    records_case = SOURCE.index("case 'records':")
    records_end = SOURCE.index("case 'schedule_rules':", records_case)
    records_block = SOURCE[records_case:records_end]

    assert clear in records_block
    assert records_block.index(clear) < records_block.index("for (const record of recordEntries)")


def test_records_backup_restore_accepts_single_day_entries_without_erasing_other_days():
    records_case = SOURCE[SOURCE.index("case 'records':"):SOURCE.index("case 'schedule_rules':")]
    assert "const recordEntries = Array.isArray(data) ? data : [data]" in records_case
    assert "recordEntries.every(isRecordBackupEntry)" in records_case
    assert "if (Array.isArray(data))" in records_case
    assert "throw new Error('Invalid records backup')" in records_case


def test_manual_plans_backup_restore_replaces_the_existing_snapshot():
    clear = "await clear(STORE_NAMES.MANUAL_PLANS)"
    plans_case = SOURCE.index("case 'manual_plans':")
    plans_end = SOURCE.index("  }\n\n  // Normal backup recovery", plans_case)
    plans_block = SOURCE[plans_case:plans_end]

    assert clear in plans_block
    assert plans_block.index(clear) < plans_block.index("for (const [date, planName]")
