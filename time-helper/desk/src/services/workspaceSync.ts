import { TodoService } from './todoService'
import type { TimeRecord } from '@/types'
import { getRawAll, STORE_NAMES } from '@/storage'
import { getPlanTasks, listPlanSummaries, planDataSource } from './planGateway'

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

/** Keep active todos derived from a plan task aligned after task edits. */
export async function syncTodosFromPlanTask(planId: string, planTaskIds: string | string[], title: string, minutes: number): Promise<number> {
  const identifiers = new Set(Array.isArray(planTaskIds) ? planTaskIds.map(String) : [String(planTaskIds)])
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && Boolean(todo.related_plan_task_id && identifiers.has(String(todo.related_plan_task_id)))
    && !['archived', 'cancelled'].includes(todo.status)
  )

  for (const todo of linked) {
    await TodoService.update(todo.id, {
      title,
      time_estimate: Math.max(0, Number(minutes) || 0),
      estimated_time: Math.max(0, Number(minutes) || 0),
    })
  }
  return linked.length
}

/** Refresh system-derived plan descriptions without overwriting user text. */
export async function syncTodoDescriptionsFromPlan(planId: string, previousName: string, nextName: string): Promise<number> {
  if (previousName === nextName) return 0
  const todos = await TodoService.list()
  const linked = todos.filter((todo) =>
    todo.related_plan_id === String(planId)
    && todo.description === previousName
    && !['archived', 'cancelled'].includes(todo.status)
  )
  for (const todo of linked) {
    await TodoService.update(todo.id, { description: nextName })
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

/**
 * Remove plan-task references that are provably stale after imports or soft
 * deletes. If the plan gateway is unavailable, leave all links untouched.
 */
export async function repairTodoPlanTaskLinks(): Promise<number> {
  try {
    const todos = await TodoService.list()
    const linkedTodos = todos.filter((todo) => todo.related_plan_id && todo.related_plan_task_id)
    if (!linkedTodos.length) return 0

    const summaries = await listPlanSummaries()
    // A cached snapshot is intentionally read-only and may be incomplete or
    // stale. Never unlink user relations based on absence from that snapshot.
    if (planDataSource.value === 'cache') return 0
    const planIds = new Set(summaries.map((plan) => String(plan.id)))
    const taskIdsByPlan = new Map<string, Set<string>>()
    for (const planId of new Set(linkedTodos.map((todo) => String(todo.related_plan_id)))) {
      if (!planIds.has(planId)) {
        taskIdsByPlan.set(planId, new Set())
        continue
      }
      try {
        const tasks = await getPlanTasks(planId)
        taskIdsByPlan.set(planId, new Set(tasks.flatMap((task) => [String(task.internal_id), String(task.display_id)])))
      } catch {
        // A single plan may be temporarily unavailable; do not repair it.
      }
    }

    let repaired = 0
    for (const todo of linkedTodos) {
      const planId = String(todo.related_plan_id)
      const taskIds = taskIdsByPlan.get(planId)
      if (!taskIds || taskIds.has(String(todo.related_plan_task_id))) continue
      await TodoService.update(todo.id, {
        related_plan_id: undefined,
        related_plan_task_id: undefined,
      })
      repaired += 1
    }
    return repaired
  } catch {
    return 0
  }
}
