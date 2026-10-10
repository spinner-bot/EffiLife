import { TodoService } from './todoService'
import type { TimeRecord } from '@/types'
import { getRawAll, set as idbSet, STORE_NAMES } from '@/storage'
import { getPlanTasks, listPlanSummaries, planDataSource } from './planGateway'

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
    const todos = await TodoService.list()
    const todoIds = new Set(todos.map((todo) => todo.id))
    const recordIds = new Set<string>()
    let repaired = 0
    for (const entry of entries) {
      if (!Array.isArray(entry.value)) continue
      let entryChanged = false
      const nextRecords = (entry.value as TimeRecord[]).map((record) => {
        if (record && typeof record.id === 'string') recordIds.add(record.id)
        if (!record?.todo_id || todoIds.has(record.todo_id)) return record
        const nextRecord = { ...record }
        delete nextRecord.todo_id
        entryChanged = true
        repaired += 1
        return nextRecord
      })
      if (entryChanged) {
        const recordEntry = entry as { key?: string }
        if (typeof recordEntry.key !== 'string') return 0
        await idbSet(STORE_NAMES.RECORDS, recordEntry.key, nextRecords)
      }
      for (const record of nextRecords) {
        if (record && typeof record.id === 'string') {
          recordIds.add(record.id)
        }
      }
    }
    for (const todo of todos) {
      const links = todo.related_time_record_ids || []
      const validLinks = [...new Set(links.filter((id) => recordIds.has(id)))]
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
        // An absent active summary is not proof that the plan was deleted:
        // archived plans and temporarily incomplete service indexes must keep
        // their recoverable TD relation until a concrete task list is read.
        continue
      }
      try {
        const tasks = await getPlanTasks(planId)
        // A task request may fall back to the local snapshot after the
        // summary request succeeded. That snapshot is not authoritative for
        // destructive link repair; leave all relations untouched.
        if (String(planDataSource.value) === 'cache') return 0
        // TD relations persist the stable PH internal ID. A display ID is a
        // projection and can be reused after soft deletion (for example, the
        // old A3 may become the displayed A2), so it must never validate a
        // persisted cross-module relation.
        taskIdsByPlan.set(planId, new Set(tasks.map((task) => String(task.internal_id))))
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
