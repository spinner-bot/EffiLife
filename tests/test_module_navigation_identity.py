from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "time-helper/desk/src/App.vue").read_text(encoding="utf-8")


def test_desktop_navigation_marks_th_ph_and_td_as_separate_modules():
    assert 'class="global-nav-module-code" aria-hidden="true">PH</span>' in APP
    assert 'class="global-nav-module-code" aria-hidden="true">TH</span>' in APP
    assert 'class="global-nav-module-code" aria-hidden="true">TD</span>' in APP


def test_workspace_navigation_exposes_module_responsibilities_as_titles():
    assert ':title="t(\'plans.moduleDescription\')"' in APP
    assert ':title="t(\'home.timeModuleSummary\')"' in APP
    assert ':title="t(\'tasks.moduleDescription\')"' in APP
