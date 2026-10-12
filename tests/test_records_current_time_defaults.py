from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "RecordsView.vue").read_text(encoding="utf-8")
PLAN_VIEW = (ROOT / "time-helper" / "desk" / "src" / "views" / "PlanView.vue").read_text(encoding="utf-8")
DEFAULTS = (ROOT / "time-helper" / "desk" / "src" / "services" / "recordDefaults.ts").read_text(encoding="utf-8")


def test_new_time_record_form_defaults_to_current_local_time():
    assert "export function currentRecordDefaults(now = new Date())" in DEFAULTS
    assert "const startMinutes = now.getHours() * 60 + now.getMinutes()" in DEFAULTS
    assert "formStart.value = defaults.start" in VIEW
    assert "formStart.value = defaults.start" in PLAN_VIEW
    assert "formDurationTime.value = defaults.reference" in VIEW
    assert "formDurationTime.value = defaults.reference" in PLAN_VIEW


def test_current_time_defaults_clamp_the_default_end_at_midnight():
    assert "const availableMinutes = Math.max(1, 24 * 60 - startMinutes)" in DEFAULTS
    assert "end: formatInputClock(startMinutes + defaultDuration)" in DEFAULTS
    assert "Math.min(24 * 60, Math.trunc(totalMinutes))" in DEFAULTS


def test_linked_todo_entry_prefills_record_content_without_removing_editability():
    assert "const linkedTodo = todos.value.find((todo) => todo.id === todoId)" in VIEW
    assert "if (!formContent.value.trim()) formContent.value = linkedTodo.title" in VIEW
