from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_import_does_not_leave_stale_plan_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    mobile_branch = source.index("if (getPlanRuntime() === 'mobile-unavailable')")
    desktop_branch = source.index("} else {\n      await clearPlanHelperData()", mobile_branch)
    assert "await idbClear(STORE_NAMES.PLAN_HELPER_SNAPSHOT)" in source[mobile_branch:desktop_branch]
    assert source.count("await clearPlanHelperData()") >= 2
    assert "warnings.push(translate('settings.archive.planNotRestored'" in source[desktop_branch:]


def test_legacy_archive_without_plan_helper_preserves_existing_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "planHelper?: PlanHelperData" in source
    assert "planHelper: legacy.planHelper" in source
    assert "if (data.planHelper === undefined)" in source
    assert "Legacy archives may not contain plan-helper data" in source
