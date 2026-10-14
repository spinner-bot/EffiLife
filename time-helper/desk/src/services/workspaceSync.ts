import { TodoService, type UnifiedTodo } from './todoService'
import type { TimeRecord } from '@/types'
import { del as idbDelete, getAll, getRawAll, set as idbSet, set as storageSet, STORE_NAMES } from '@/storage'
import { completePlanTask, getPlanTasks, listPlanSummaries, planDataSource } from './planGateway'

export class PlanTodoSyncError extends Error {
  readonly phase = 'todo' as const

  constructor(readonly cause: unknown) {
    super('The linked todo could not be completed after the plan task was completed')
    this.name = 'PlanTodoSyncError'
  }
}

export interface PendingPlanTodoSync {
  key: string
  planId: string
  planTaskId: string
  createdAt: string
}

function pendingPlanTodoSyncKey(planId: string, planTaskId: string): string {
  return `${String(planId)}:${String(planTaskId)}`
}

/** Persist an explicit cross-module completion that needs a later retry. */
export async function queuePendingPlanTodoSync(planId: string, planTaskId: string): Promise<void> {
  try {
    const normalizedPlanId = String(planId)
    const normalizedTaskId = String(planTaskId)
    await storageSet(STORE_NAMES.PENDING_PLAN_TODO_SYNC, pendingPlanTodoSyncKey(normalizedPlanId, normalizedTaskId), {
      key: pendingPlanTodoSyncKey(normalizedPlanId, normalizedTaskId),
      planId: normalizedPlanId,
      planTaskId: normalizedTaskId,
      createdAt: new Date().toISOString(),
    } satisfies PendingPlanTodoSync)
  } catch (error) {
    console.warn('Failed to persist pending plan/todo sync:', error)
  }
}

export async function clearPendingPlanTodoSync(planId: string, planTaskId: string): Promise<void> {
  try {
    await idbDelete(STORE_NAMES.PENDING_PLAN_TODO_SYNC, pendingPlanTodoSyncKey(planId, planTaskId))
  } catch (error) {
    // The user operation has already succeeded; a stale queue entry is safe
    // to retry later and must not turn success into a false error.
    console.warn('Failed to clear pending plan/todo sync:', error)
  }
}

/** Retry persisted projection failures after startup without blocking the shell. */
export async function repairPendingPlanTodoSync(): Promise<number> {
  let repaired = 0
  let pending: PendingPlanTodoSync[]
  try {
    pending = await getAll<PendingPlanTodoSync>(STORE_NAMES.PENDING_PLAN_TODO_SYNC)
  } catch {
    return 0
  }
  for (const item of pending) {
    if (!item?.planId || !item.planTaskId) continue
    try {
      await completeLinkedPlanTodo(item.planId, item.planTaskId)
      await clearPendingPlanTodoSync(item.planId, item.planTaskId)
      repaired += 1
    } catch {
      // Keep the entry for a later startup or manual retry.
    }
  }
  return repaired
}

/**
 * Complete a TD item and its PH projection in the documented order.
 *
 * PH must succeed before TD is changed. The two stores are not transactional;
 * if the TD write fails after PH succeeds, the caller keeps the PH result and
 * reports the recoverable projection error.
 */
export async function completeTodoWithPlan(todo: UnifiedTodo): Promise<UnifiedTodo> {
  if (todo.related_plan_id && todo.related_plan_task_id) {
    await completePlanTask(todo.related_plan_id, todo.related_plan_task_id)
  }
  try {
    return await TodoService.complete(todo.id)
  } catch (error) {
    if (todo.related_plan_id && todo.related_plan_task_id) {
      throw new PlanTodoSyncError(error)
    }
    throw error
  }
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

  const updated: typeof linked = []
  try {
    for (const todo of linked) {
      await TodoService.update(todo.id, {
        related_plan_id: undefined,
        related_plan_task_id: undefined,
      })
      updated.push(todo)
    }
  } catch (error) {
    for (const todo of updated) {
      try {
        await TodoService.update(todo.id, {
          related_plan_id: todo.related_plan_id,
          related_plan_task_id: todo.related_plan_task_id,
        })
      } catch (rollbackError) {
        console.error('Failed to roll back plan-task todo unlink:', rollbackError)
      }
    }
    throw error
  }
  return linked.length
}

/**
 * Project PH completion onto every exact TD relation.
 *
 * PH remains the source of truth for plan progress. The TD records are
 * projections, so a failed projection must be reported to the caller rather
 * than rolling back a successful PH mutation across storage boundaries.
 */
export async function completeLinkedPlanTodo(planId: string, planTaskId: string): Promise<number> {
  const linked = (await TodoService.list()).filter((todo) => (
    todo.related_plan_id === String(planId)
    && todo.related_plan_task_id === String(planTaskId)
    && todo.status !== 'completed'
    && todo.status !== 'archived'
    && todo.status !== 'cancelled'
  ))
  let firstError: unknown = null
  for (const todo of linked) {
    try {
      await TodoService.complete(todo.id)
    } catch (error) {
      // PH remains completed, but one TD projection must not prevent the
      // remaining exact relations from being attempted. The caller still
      // receives an error so the partial projection stays visible and
      // recoverable instead of being mistaken for success.
      firstError ??= error
    }
  }
  if (firstError) throw firstError
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
    const changedRecords: Array<{ key: string; previous: TimeRecord[]; next: TimeRecord[] }> = []
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
        if (typeof recordEntry.key !== 'string') throw new Error('Record repair entry has no storage key')
        changedRecords.push({
          key: recordEntry.key,
          previous: entry.value as TimeRecord[],
          next: nextRecords,
        })
      }
      for (const record of nextRecords) {
        if (record && typeof record.id === 'string') {
          recordIds.add(record.id)
        }
      }
    }
    const changedTodos: Array<{ id: string; links: string[] }> = []
    for (const todo of todos) {
      const links = todo.related_time_record_ids || []
      const validLinks = [...new Set(links.filter((id) => recordIds.has(id)))]
      if (validLinks.length === links.length) continue
      changedTodos.push({ id: todo.id, links })
      repaired += 1
    }
    try {
      for (const entry of changedRecords) {
        await idbSet(STORE_NAMES.RECORDS, entry.key, entry.next)
      }
      for (const todo of changedTodos) {
        const validLinks = [...new Set((todos.find((item) => item.id === todo.id)?.related_time_record_ids || []).filter((id) => recordIds.has(id)))]
        await TodoService.update(todo.id, { related_time_record_ids: validLinks })
      }
    } catch (error) {
      for (const todo of changedTodos) {
        try {
          await TodoService.update(todo.id, { related_time_record_ids: todo.links })
        } catch (rollbackError) {
          console.error('Failed to roll back todo/time-record link repair:', rollbackError)
        }
      }
      for (const entry of changedRecords) {
        try {
          await idbSet(STORE_NAMES.RECORDS, entry.key, entry.previous)
        } catch (rollbackError) {
          console.error('Failed to roll back repaired time records:', rollbackError)
        }
      }
      throw error
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
    const repairedTodos: typeof linkedTodos = []
    try {
      for (const todo of linkedTodos) {
        const planId = String(todo.related_plan_id)
        const taskIds = taskIdsByPlan.get(planId)
        if (!taskIds || taskIds.has(String(todo.related_plan_task_id))) continue
        await TodoService.update(todo.id, {
          related_plan_id: undefined,
          related_plan_task_id: undefined,
        })
        repairedTodos.push(todo)
        repaired += 1
      }
    } catch (error) {
      for (const todo of repairedTodos) {
        try {
          await TodoService.update(todo.id, {
            related_plan_id: todo.related_plan_id,
            related_plan_task_id: todo.related_plan_task_id,
          })
        } catch (rollbackError) {
          console.error('Failed to roll back plan-task link repair:', rollbackError)
        }
      }
      throw error
    }
    return repaired
  } catch {
    return 0
  }
}
