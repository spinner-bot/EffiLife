from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_task_center_does_not_hardcode_time_unit_or_category_aria_label():
    source = TASKS.read_text(encoding="utf-8")
    assert "{{ t('tasks.minutesShort') }}" in source
    assert 'aria-label="category name"' not in source


def test_task_time_unit_has_bilingual_catalog_entries():
    source = I18N.read_text(encoding="utf-8")
    assert "'tasks.minutesShort': '分钟'" in source
    assert "'tasks.minutesShort': 'min'" in source
