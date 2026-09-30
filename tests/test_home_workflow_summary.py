from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_home_summary_aggregates_three_unified_workstreams():
    assert "const todayRecordHours = computed(() => appStore.todayRecords.reduce" in HOME
    assert 'class="workflow-summary"' in HOME
    assert "home.recordedToday" in HOME
    assert "home.eventPlanProgress" in HOME
    assert "home.activeTodos" in HOME
    assert "router.push('/time')" in HOME
    assert "router.push('/plans')" in HOME
    assert "router.push('/tasks')" in HOME


def test_home_workflow_summary_has_bilingual_copy():
    for key in ("home.workflowSummary", "home.recordedToday", "home.eventPlanProgress", "home.activeTodos"):
        assert I18N.count(f"'{key}':") == 2
