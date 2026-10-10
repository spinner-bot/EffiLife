from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANS = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_plan_center_filters_active_and_archived_plans_locally():
    assert "const planSearch = ref('')" in PLANS
    assert "const filteredPlans = computed(() =>" in PLANS
    assert "const filteredArchives = computed(() =>" in PLANS
    assert "v-for=\"plan in filteredPlans\"" in PLANS
    assert "v-for=\"archive in filteredArchives\"" in PLANS


def test_plan_center_filter_is_localized_and_accessible():
    assert '<label v-if="plans.length > 1 || archives.length > 1" class="plans-search">' in PLANS
    assert 'v-model="planSearch"' in PLANS
    assert I18N.count("'plans.searchLabel'") == 2
    assert I18N.count("'plans.searchPlaceholder'") == 2


def test_plan_center_search_uses_shared_locale_independent_date_tokens():
    assert "import { dateSearchText } from '@/services/dateSearch'" in PLANS
    assert "dateSearchText(plan.date)" in PLANS
    assert "dateSearchText(archive.date)" in PLANS
