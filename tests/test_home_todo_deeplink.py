from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "time-helper" / "desk" / "src" / "views" / "HomeView.vue"
TASKS = ROOT / "time-helper" / "desk" / "src" / "views" / "TaskCenterView.vue"


def test_home_todo_rows_preserve_the_selected_todo():
    source = HOME.read_text(encoding="utf-8")
    assert "router.push({ path: '/tasks', query: { todo: todo.id } })" in source


def test_task_center_consumes_home_todo_deeplink():
    source = TASKS.read_text(encoding="utf-8")
    assert "route.query.todo" in source
    assert "document.getElementById(`todo-${targetId}`)?.scrollIntoView" in source


def test_task_center_explains_stale_todo_deeplink_without_blocking_the_center():
    source = TASKS.read_text(encoding="utf-8")
    assert "const missingTodoTargetId = ref<string | null>(null)" in source
    assert "missingTodoTargetId.value = targetId" in source
    assert 'class="task-deeplink-note"' in source
    assert "tasks.todoTargetMissing" in source


def test_home_event_plan_summary_has_aggregate_progress_visual():
    source = HOME.read_text(encoding="utf-8")
    assert "const eventPlanProgress = computed" in source
    assert "event-overview-progress-track" in source
    assert "eventPlanProgress}%`" in source


def test_home_event_plan_summary_avoids_nested_interactive_containers():
    source = HOME.read_text(encoding="utf-8")
    assert '<section class="event-overview-card">' in source
    assert 'class="event-overview-header event-overview-header-action"' in source
    assert 'role="link" tabindex="0"' not in source
    assert "activateEventOverview" not in source


def test_home_event_plan_summary_discloses_cached_source():
    source = HOME.read_text(encoding="utf-8")
    assert "planDataSource" in source
    assert "isEventPlanSnapshot" in source
    assert "plans.cachedTitle" in source


def test_home_event_plan_summary_discloses_mobile_snapshot_source():
    source = HOME.read_text(encoding="utf-8")
    assert "planDataSource.value === 'mobile'" in source
    assert "plans.mobileLocalTitle" in source
