from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "time-helper" / "desk" / "src" / "services" / "todoService.ts"


def test_todo_read_modify_write_mutations_are_serialized_per_task():
    source = SERVICE.read_text(encoding="utf-8")
    assert "const todoWriteQueues = new Map<string, Promise<unknown>>()" in source
    assert "function enqueueTodoWrite<T>(id: string, operation: () => Promise<T>): Promise<T>" in source
    assert "const previous = todoWriteQueues.get(id) || Promise.resolve()" in source
    assert "async function mutateTodo(id: string, patchFactory: (current: UnifiedTodo) => Partial<UnifiedTodo>)" in source
    source = source.split("export const TodoService =", 1)[1]
    for marker in (
        "async update(id: string, patch: Partial<UnifiedTodo>)",
        "async addSubtask(id: string, title: string)",
        "async toggleSubtask(id: string, subtaskId: string)",
        "async removeSubtask(id: string, subtaskId: string)",
        "async remove(id: string): Promise<void>",
        "async trackTime(id: string, minutes: number, timeRecordId?: string | string[])",
        "async adjustTrackedTime(id: string, deltaMinutes: number)",
    ):
        block = source.split(marker, 1)[1].split("\n  },", 1)[0]
        assert "mutateTodo(id" in block or "enqueueTodoWrite(id" in block


def test_subtask_and_time_aggregation_mutate_inside_the_serialized_callback():
    source = SERVICE.read_text(encoding="utf-8")
    assert "subtasks: [...current.subtasks" in source
    assert "const existingRecordIds = current.related_time_record_ids || []" in source
    assert "time_spent: (current.time_spent || 0) + addedMinutes" in source
    assert "time_spent: Math.max(0, Number(current.time_spent || 0) + deltaMinutes)" in source
