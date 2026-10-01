from pathlib import Path


VIEW = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue").read_text(encoding="utf-8")
I18N = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_task_empty_state_distinguishes_filters_from_empty_data():
    assert "const hasTaskContentFilters = computed" in VIEW
    assert "const taskEmptyTitle = computed" in VIEW
    assert "@click=\"clearTaskContentFilters\"" in VIEW
    assert "'tasks.emptyFiltered'" in I18N
    assert "'tasks.clearFilters'" in I18N
