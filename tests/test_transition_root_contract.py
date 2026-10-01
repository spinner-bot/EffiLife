from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_VIEW = ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue"


def test_plan_workspace_transition_keeps_one_root_panel():
    source = PLAN_VIEW.read_text(encoding="utf-8")
    transition = source.split('<Transition name="tab-fade" mode="out-in">', 1)[1].split("</Transition>", 1)[0]

    # Vue's Transition requires exactly one direct rendered child. The
    # overview panel is the stable root; the other manage views stay inside
    # its conditional branch and must not become sibling transition roots.
    assert '<div v-if="manageView === \'overview\'" key="overview" class="pv-panel">' in transition
    assert '<template v-else-if="manageView ===' in transition
    assert transition.count('<div v-if="manageView === \'overview\'"') == 1
    assert transition.index('<template v-else-if="manageView ===') > transition.index('<div v-if="manageView ===')


def test_plan_workspace_transition_keeps_view_branches_inside_root_panel():
    source = PLAN_VIEW.read_text(encoding="utf-8")
    transition = source.split('<Transition name="tab-fade" mode="out-in">', 1)[1].split("</Transition>", 1)[0]
    root_start = transition.index('<div v-if="manageView === \'overview\'"')
    root_end = transition.rfind("</div>")
    root = transition[root_start:root_end]

    assert root.count('<template v-else-if="manageView ===') == 4
    assert "manageView === 'plans'" in root
    assert "manageView === 'editPlan'" in root
    assert "manageView === 'rules'" in root
    assert "manageView === 'editRule'" in root
    assert "manageView === 'tempChange'" in root
