from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "time-helper" / "desk" / "src" / "services" / "ArchiveService.ts"


def test_archive_import_clears_only_explicitly_empty_plan_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    mobile_branch = source.index("if (getPlanRuntime() === 'mobile-unavailable')")
    unavailable_branch = source.index("// An unavailable PH export is an incomplete snapshot", mobile_branch)
    assert "await idbClear(STORE_NAMES.PLAN_HELPER_SNAPSHOT)" in source[mobile_branch:unavailable_branch]
    assert "await clearPlanHelperData()" not in source[unavailable_branch:source.index("notifyWorkspaceChanged('archive')", unavailable_branch)]
    assert "warnings.push(translate('settings.archive.planNotRestored'" in source[unavailable_branch:]
    assert "if (data.planHelper?.available && Array.isArray(data.planHelper.plans))" in source


def test_legacy_archive_without_plan_helper_preserves_existing_snapshot():
    source = ARCHIVE.read_text(encoding="utf-8")
    assert "planHelper?: PlanHelperData" in source
    assert "planHelper: legacy.planHelper" in source
    assert "if (data.planHelper === undefined)" in source
    assert "Legacy archives may not contain plan-helper data" in source
