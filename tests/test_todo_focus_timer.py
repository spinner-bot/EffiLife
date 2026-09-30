from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"
I18N = ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts"


def test_focus_timer_reuses_unified_time_record_and_todo_tracking():
    source = TASKS.read_text(encoding="utf-8")
    assert "const focusTodoId = ref<string | null>(null)" in source
    assert "function startFocus(todo: UnifiedTodo)" in source
    assert "async function stopFocus(todo: UnifiedTodo)" in source
    assert "await persistTodoTime(todo, minutes, startedAt)" in source
    assert "DataService.saveRecord" in source
    assert "TodoService.trackTime" in source
    assert "focusTodoId === todo.id ? stopFocus(todo) : startFocus(todo)" in source


def test_focus_timer_copy_exists_in_both_locales():
    source = I18N.read_text(encoding="utf-8")
    for key in ("tasks.startFocus", "tasks.stopFocus", "tasks.focusHint"):
        assert source.count(f"'{key}'") == 2


def test_recorded_todo_time_confirms_cross_module_sync():
    source = TASKS.read_text(encoding="utf-8")
    catalog = I18N.read_text(encoding="utf-8")
    assert "notifyToast(t('tasks.timeRecorded', { minutes }), 'success')" in source
    assert catalog.count("'tasks.timeRecorded':") == 2


def test_focus_timer_is_saved_when_task_center_unmounts():
    source = TASKS.read_text(encoding="utf-8")
    assert "onUnmounted(() => {" in source
    assert "const activeFocusTodo = todos.value.find" in source
    assert "if (activeFocusTodo)" in source
    assert "void stopFocus(activeFocusTodo).catch((error) =>" in source
    assert "clearFocusTimer()" in source
