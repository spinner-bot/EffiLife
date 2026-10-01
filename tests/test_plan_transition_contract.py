from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")


def test_plan_workspace_transition_keeps_conditional_roots_adjacent():
    transition_start = PLAN_VIEW.index('<Transition name="tab-fade" mode="out-in">')
    transition_end = PLAN_VIEW.index('</Transition>', transition_start)
    transition = PLAN_VIEW[transition_start:transition_end]

    assert '<div v-if="manageView === \'overview\'" key="overview"' in transition
    assert '<div v-else key="manage"' in transition
    lines = transition.splitlines()
    else_index = next(index for index, line in enumerate(lines) if '<div v-else key="manage"' in line)
    previous_non_empty = next(line.strip() for line in reversed(lines[:else_index]) if line.strip())
    assert previous_non_empty == '</div>'
