import { TodoService } from './todoService'
import type { TimeRecord } from '@/types'
import { getRawAll, STORE_NAMES } from '@/storage'

/**
 * Complete every unified todo linked to a plan task.
 *
 * Plan-helper keeps its original task identity model, so this coordinator only
 * updates the unified todo side after the plan API has accepted completion.
 */
export async function completeLinkedTodos(planId: string, planTaskIds: string | string[]): Promise<number> {
  const identifiers = new Set(Array.isArray(planTaskIds) ? planTaskIds.map(String) : [String(planTaskIds)])
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && Boolean(todo.related_plan_task_id && identifiers.has(String(todo.related_plan_task_id)))
    && todo.status !== 'completed'
  )

  for (const todo of linked) {
    await TodoService.complete(todo.id)
  }
  return linked.length
}

/**
 * Remove a stale plan-task reference while keeping the user's todo intact.
 * Plan-helper may soft-delete the task, so retaining the old identifier would
 * make a later todo completion call target a task that can no longer finish.
 */
export async function unlinkTodosFromPlanTask(planId: string, planTaskId: string): Promise<number> {
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && todo.related_plan_task_id === String(planTaskId)
  )

  for (const todo of linked) {
    await TodoService.update(todo.id, {
      related_plan_id: undefined,
      related_plan_task_id: undefined,
    })
  }
  return linked.length
}

/** Remove a deleted time-record ID without changing the todo's historical total. */
export async function unlinkTodoFromTimeRecord(record: TimeRecord): Promise<boolean> {
  if (!record.id || !record.todo_id) return false
  const todo = (await TodoService.list()).find((item) => item.id === record.todo_id)
  if (!todo?.related_time_record_ids?.includes(record.id)) return false
  await TodoService.update(todo.id, {
    related_time_record_ids: todo.related_time_record_ids.filter((id) => id !== record.id),
  })
  return true
}

/**
 * Repair stale links left by older versions. If the record store cannot be
 * read, do nothing rather than interpreting an unavailable store as empty.
 */
export async function repairTodoTimeRecordLinks(): Promise<number> {
  try {
    const entries = await getRawAll<{ value?: unknown }>(STORE_NAMES.RECORDS)
    const recordIds = new Set<string>()
    for (const entry of entries) {
      if (!Array.isArray(entry.value)) continue
      for (const record of entry.value) {
        if (record && typeof record === 'object' && typeof (record as TimeRecord).id === 'string') {
          recordIds.add((record as TimeRecord).id as string)
        }
      }
    }
    const todos = await TodoService.list()
    let repaired = 0
    for (const todo of todos) {
      const links = todo.related_time_record_ids || []
      const validLinks = links.filter((id) => recordIds.has(id))
      if (validLinks.length === links.length) continue
      await TodoService.update(todo.id, { related_time_record_ids: validLinks })
      repaired += 1
    }
    return repaired
  } catch {
    return 0
  }
}
