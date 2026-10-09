from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_plan_status_filter_is_explicit_and_keeps_empty_plans_active():
    assert "const planFilter = ref<'all' | 'active' | 'completed'>('all')" in VIEW
    assert "const hasTasks = (plan.total_tasks || 0) > 0" in VIEW
    assert "planFilter.value === 'completed' && isCompleted" in VIEW
    assert "planFilter.value === 'active' && !isCompleted" in VIEW


def test_plan_status_filter_composes_with_search_and_exposes_pressed_state():
    assert "matchesFilter && matchesQuery" in VIEW
    assert 'role="group" :aria-label="t(\'plans.statusFilterLabel\')"' in VIEW
    assert ':aria-pressed="planFilter === filter"' in VIEW
    assert "t(`plans.statusFilter.${filter}`)" in VIEW
    assert VIEW.count("'plans.statusFilterLabel':") == 0
    assert I18N.count("'plans.statusFilterLabel':") == 2
    for key in ("all", "active", "completed"):
        assert I18N.count(f"'plans.statusFilter.{key}':") == 2


def test_plan_status_filter_is_responsive_and_loading_safe():
    assert ".plans-filter-button:disabled" in VIEW
    mobile = VIEW.split("@media (max-width: 760px)", 1)[1]
    assert ".plans-list-tools { align-items: stretch; flex-direction: column;" in mobile
