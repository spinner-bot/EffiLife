from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "time-helper" / "desk" / "src" / "services" / "planGateway.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_mobile_plan_groups_preserve_nested_but_reject_crossing_ranges():
    source = GATEWAY.read_text(encoding="utf-8")
    assert "function mobileGroupCrossesExisting" in source
    assert "existingStart < startIndex && startIndex < existingEnd && existingEnd < endIndex" in source
    assert "startIndex < existingStart && existingStart < endIndex && endIndex < existingEnd" in source
    assert "if (mobileGroupCrossesExisting(section.group, startIndex, endIndex))" in source
    assert "throw new Error(translate('plans.groupConflict'))" in source
    assert "section.group[`${startIndex}_${endIndex}`]" in source


def test_mobile_plan_group_validation_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert "'plans.groupRangeInvalid': '任务组范围无效'" in source
    assert "'plans.groupConflict': '任务组范围不能与已有任务组交叉'" in source
    assert "'plans.groupRangeInvalid': 'Invalid task-group range'" in source
    assert "'plans.groupConflict': 'Task-group ranges cannot cross existing groups'" in source

