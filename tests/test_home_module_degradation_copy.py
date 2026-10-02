from pathlib import Path


HOME = (Path(__file__).parents[1] / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_home_module_summary_names_the_unavailable_th_module():
    assert "timeSummaryUnavailable ? t('home.timeUnavailable') : t('home.timeModuleSummary')" in HOME


def test_home_module_summary_names_the_unavailable_ph_module():
    assert "eventPlanState === 'unavailable'" in HOME
    assert "t('home.eventPlansUnavailableMobile')" in HOME
    assert "t('home.eventPlansUnavailable')" in HOME


def test_home_module_summary_names_the_unavailable_td_module():
    assert "todoSummaryUnavailable ? t('home.todosUnavailable') : t('home.todoModuleSummary')" in HOME
