import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { findPlan, findNode, categoryFor } from './plans'
import { requireCondition, requireTitle } from './errors'
import { instant, minutesBetween, referenceFor } from './time'
import { applyTodoCommand } from './todo-commands'

function removeRecords(workspace: Workspace, ids: Set<string>) {
  workspace.records = workspace.records.filter(item => !ids.has(item.id))
  for (const plan of workspace.plans) for (const log of plan.logs) log.recordIds = log.recordIds.filter(id => !ids.has(id))
  for (const todo of workspace.todos) todo.recordIds = todo.recordIds.filter(id => !ids.has(id))
}

export function applyRecordCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (command.type === 'recordAction') {
    requireCondition(!command.taskId || command.planId, 'validation.planMissing')
    const plan = command.planId ? findPlan(workspace, command.planId) : undefined
    requireCondition(!plan?.archivedAt, 'validation.planArchived')
    const task = plan && command.taskId ? findNode(plan, command.taskId) : undefined
    const todo = command.todoId ? workspace.todos.find(item => item.id === command.todoId) : undefined
    requireCondition(!command.todoId || todo, 'validation.todoMissing')
    requireCondition(!todo || !['archived', 'cancelled'].includes(todo.status), 'validation.todoArchived')
    requireCondition(!command.completeTodo || todo, 'validation.todoMissing')
    requireCondition(!task || task.kind === 'task', 'validation.taskRequired')
    requireCondition(!task?.deletedAt, 'validation.taskDeleted')
    requireCondition(!command.completeTask || task, 'validation.taskRequired')
    requireCondition(Boolean(command.startAt) === Boolean(command.endAt), 'validation.timeIncomplete')
    const hasTime = Boolean(command.startAt && command.endAt)
    requireCondition(plan || hasTime, 'validation.timeRequired')
    const occurredAt = instant(command.occurredAt || command.endAt || context.now)
    const title = requireTitle(command.title || task?.title || todo?.title || command.content)
    const categoryId = command.categoryId || (plan ? categoryFor(plan, task?.id) : todo?.categoryId || 'life')
    requireCondition(workspace.categories.some(category => category.id === categoryId), 'validation.categoryMissing')
    const hint = referenceFor(workspace, occurredAt)
    const logId = plan ? context.id() : undefined
    let recordId: string | undefined
    if (hasTime) {
      const minutes = minutesBetween(command.startAt!, command.endAt!)
      requireCondition(command.expectedMinutes === undefined || (Number.isFinite(command.expectedMinutes) && Math.abs(command.expectedMinutes - minutes) < 1e-6), 'validation.durationMismatch')
      recordId = context.id()
      workspace.records.push({
        id: recordId, title, note: command.content.trim(), categoryId,
        startAt: instant(command.startAt!), endAt: instant(command.endAt!),
        planId: plan?.id, taskId: task?.id, logId, todoId: todo?.id,
        timing: command.timing || 'actual', source: 'manual',
      })
    }
    if (plan && logId) {
      plan.logs.push({
        id: logId, taskId: task?.id, occurredAt, content: command.content.trim() || title,
        kind: command.completeTask ? 'completion' : 'progress',
        recordIds: recordId ? [recordId] : [], timingReference: hint,
      })
      plan.updatedAt = context.now
      if (task && command.completeTask) task.completedAt = occurredAt
    }
    if (todo) {
      if (recordId) todo.recordIds.push(recordId)
      todo.updatedAt = context.now
      if (command.completeTodo) applyTodoCommand(workspace, { type: 'setTodoStatus', todoId: todo.id, status: 'completed', occurredAt }, context)
    }
    return { recordId, logId, entityId: task?.id || plan?.id || recordId }
  }
  if (command.type === 'updateRecord') {
    const record = workspace.records.find(item => item.id === command.recordId)
    requireCondition(record, 'validation.recordMissing')
    requireCondition(workspace.categories.some(category => category.id === command.categoryId), 'validation.categoryMissing')
    const minutes = minutesBetween(command.startAt, command.endAt)
    requireCondition(command.expectedMinutes === undefined || (Number.isFinite(command.expectedMinutes) && Math.abs(command.expectedMinutes - minutes) < 1e-6), 'validation.durationMismatch')
    record.title = requireTitle(command.title)
    record.note = command.note.trim()
    if (record.planId && record.logId) {
      const log = workspace.plans.find(plan => plan.id === record.planId)?.logs.find(item => item.id === record.logId)
      if (log) log.content = record.note || record.title
    }
    record.categoryId = command.categoryId
    record.startAt = instant(command.startAt)
    record.endAt = instant(command.endAt)
    return { recordId: record.id }
  }
  if (command.type === 'deleteRecord') {
    requireCondition(workspace.records.some(item => item.id === command.recordId), 'validation.recordMissing')
    removeRecords(workspace, new Set([command.recordId]))
    return { recordId: command.recordId }
  }
  if (command.type === 'updateLog') {
    const plan = findPlan(workspace, command.planId)
    const log = plan.logs.find(item => item.id === command.logId)
    requireCondition(log, 'validation.logMissing')
    log.content = requireTitle(command.content)
    for (const record of workspace.records) if (record.logId === log.id && record.planId === plan.id) record.note = log.content
    plan.updatedAt = context.now
    return { logId: log.id }
  }
  if (command.type === 'deleteLog') {
    const plan = findPlan(workspace, command.planId)
    const log = plan.logs.find(item => item.id === command.logId)
    requireCondition(log, 'validation.logMissing')
    removeRecords(workspace, new Set(log.recordIds))
    plan.logs = plan.logs.filter(item => item.id !== log.id)
    plan.updatedAt = context.now
    return { logId: log.id }
  }
  return undefined
}

