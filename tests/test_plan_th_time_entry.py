from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlansHubView.vue").read_text(encoding="utf-8")
I18N = (ROOT / "time-helper" / "desk" / "src" / "i18n" / "index.ts").read_text(encoding="utf-8")


def test_linked_ph_task_can_open_th_time_entry_without_merging_entities():
    assert "async function recordLinkedTodoTime(taskId: string): Promise<void>" in VIEW
    assert "todo.related_plan_id === planId && todo.related_plan_task_id === taskId" in VIEW
    assert "path: '/records', query: { todo: linkedTodo.id }" in VIEW
    assert "v-if=\"linkedTodoTaskIds.has(task.internal_id)\"" in VIEW
    assert "t('plans.recordTodoTime')" in VIEW


def test_ph_time_entry_handles_stale_or_unavailable_link_in_both_locales():
    assert I18N.count("'plans.todoUnavailable':") == 2
    assert "await refreshLinkedTodoTaskIds()" in VIEW
    assert "notifyToast(t('plans.todoUnavailable'), 'error')" in VIEW
