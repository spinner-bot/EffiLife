from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_task_center_computes_ranked_categories_and_reuses_filter():
    source = TASKS.read_text(encoding="utf-8")
    assert "const categorySummaries = computed" in source
    assert "Math.sqrt(items.length)" in source
    assert "category.pinned" in source
    assert "categoryFilter = item.category.id" in source
    assert "todoSettings.expandCount" in source


def test_task_center_can_expand_empty_and_lower_ranked_categories():
    source = TASKS.read_text(encoding="utf-8")
    assert "showAllCategories" in source
    assert "showEmptyCategories" in source
    assert "tasks.showMoreCategories" in source
    assert "tasks.showEmptyCategories" in source
