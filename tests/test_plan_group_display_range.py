from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_plan_group_range_is_rendered_from_visible_task_ids():
    source = VIEW.read_text(encoding="utf-8")

    assert "function groupDisplayRange" in source
    assert "task.is_active !== false" in source
    assert "first.display_id" in source
    assert "last.display_id" in source
    assert "groupDisplayRange(section, group)" in source
    assert "{{ group.key }}" not in source


def test_plan_group_empty_range_has_bilingual_copy():
    catalog = I18N.read_text(encoding="utf-8")

    assert catalog.count("'plans.groupNoActiveTasks':") == 2
