from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "time-helper" / "desk" / "src" / "components" / "GlobalSearch.vue").read_text(encoding="utf-8")


def test_global_search_uses_unwrapped_record_reader():
    assert "import { getAll, STORE_NAMES } from '@/storage'" in SOURCE
    assert "getAll<TimeRecord[]>(STORE_NAMES.RECORDS)" in SOURCE
    assert "getRawAll<TimeRecord[]>(STORE_NAMES.RECORDS)" not in SOURCE


def test_global_search_does_not_block_primary_results_on_plan_task_indexing():
    assert "async function loadPlanTaskIndex" in SOURCE
    assert "void loadPlanTaskIndex(plans.value, requestId)" in SOURCE
    assert "let searchRequestId = 0" in SOURCE


def test_global_search_indexes_active_plan_dates_for_plan_and_task_results():
    assert "import { dateSearchText } from '@/services/dateSearch'" in SOURCE
    assert "dateSearchText(plan.date)" in SOURCE
