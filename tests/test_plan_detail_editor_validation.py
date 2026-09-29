from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")


def test_plan_editors_expose_native_required_constraints():
    assert '<input v-model="planName" required />' in VIEW
    assert '<input v-model="planDate" type="date" required />' in VIEW
    assert ':placeholder="t(\'plans.sectionName\')" required />' in VIEW
    assert '<input v-model="taskContent" required autofocus />' in VIEW
    assert '<input v-model="groupTitle" required autofocus />' in VIEW
