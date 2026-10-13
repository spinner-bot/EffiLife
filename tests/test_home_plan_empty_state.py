from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")


def test_home_plan_empty_state_has_an_actionable_plan_entry():
    empty_state = HOME_VIEW.split("<template v-if=\"eventPlanState === 'ready'\">", 1)[1].split(
        "</template>\n          <span v-else-if=\"eventPlanState === 'loading'\">", 1
    )[0]

    assert 'v-if="eventPlans.length === 0"' in empty_state
    assert ':title="t(\'home.noPlanData\')"' in empty_state
    assert ':action-text="t(\'home.goToManage\')"' in empty_state
    assert 'action-route="/plans"' in empty_state


def test_home_plan_empty_state_does_not_replace_the_todo_entry():
    assert 'action-route="/tasks"' in HOME_VIEW
    assert 'class="home-module-code">PH<' in HOME_VIEW
    assert 'class="home-module-code">TD<' in HOME_VIEW
