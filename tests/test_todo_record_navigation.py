from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
DAY = ROOT / "time-helper" / "desk" / "src" / "views" / "DayDetailView.vue"
DATA = ROOT / "time-helper" / "desk" / "src" / "services" / "dataService.ts"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_todo_can_open_its_latest_record_date():
    source = TASKS.read_text(encoding="utf-8")
    assert "findRecordDatesByTodoId(todo.id)" in source
    assert "`/day/${dates[dates.length - 1]}`" in source
    assert "query: { todo: todo.id }" in source
    assert "todo.related_time_record_ids?.length" in source


def test_day_detail_highlights_linked_todo_records():
    source = DAY.read_text(encoding="utf-8")
    assert "route.query.todo" in source
    assert "record.todo_id === highlightedTodoId.value" in source
    assert "record-item-highlight" in source


def test_record_date_lookup_reads_unified_record_store():
    source = DATA.read_text(encoding="utf-8")
    assert "async findRecordDatesByTodoId(todoId: string)" in source
    assert "getRawAll<{ key?: string; value?: unknown }>(STORE_NAMES.RECORDS)" in source
    assert "record.todo_id === todoId" in source


def test_record_navigation_is_localized():
    source = I18N.read_text(encoding="utf-8")
    assert "'tasks.viewTimeRecords':" in source
    assert "'dayDetail.linkedTodo':" in source
