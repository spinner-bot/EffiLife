import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { findPlan, findNode, categoryFor } from './plans'
import { requireCondition, requireTitle } from './errors'
import { instant, minutesBetween, referenceFor } from './time'

export function applyRecordCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (command.type === 'recordAction') {
    requireCondition(!command.taskId || command.planId, 'validation.planMissing')
    const plan = command.planId ? findPlan(workspace, command.planId) : undefined
    requireCondition(!plan?.archivedAt, 'validation.planArchived')
    const task = plan && command.taskId ? findNode(plan, command.taskId) : undefined
    requireCondition(!task || task.kind === 'task', 'validation.taskRequired')
    requireCondition(!task?.deletedAt, 'validation.taskDeleted')
    requireCondition(!command.completeTask || task, 'validation.taskRequired')
    requireCondition(Boolean(command.startAt) === Boolean(command.endAt), 'validation.timeIncomplete')
    const hasTime = Boolean(command.startAt && command.endAt)
    requireCondition(plan || hasTime, 'validation.timeRequired')
    const occurredAt = instant(command.occurredAt || command.endAt || context.now)
    const title = requireTitle(command.title || task?.title || command.content)
    const categoryId = command.categoryId || (plan && task ? categoryFor(plan, task.id) : 'life')
    requireCondition(workspace.categories.some(category => category.id === categoryId), 'validation.categoryMissing')
    const hint = referenceFor(workspace, occurredAt)
    const logId = plan ? context.id() : undefined
    let recordId: string | undefined
    if (hasTime) {
      minutesBetween(command.startAt!, command.endAt!)
      recordId = context.id()
      workspace.records.push({
        id: recordId, title, note: command.content.trim(), categoryId,
        startAt: instant(command.startAt!), endAt: instant(command.endAt!),
        planId: plan?.id, taskId: task?.id, logId,
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
    return { recordId, logId, entityId: task?.id || plan?.id || recordId }
  }
  if (command.type === 'updateRecord') {
    const record = workspace.records.find(item => item.id === command.recordId)
    requireCondition(record, 'validation.recordMissing')
    requireCondition(workspace.categories.some(category => category.id === command.categoryId), 'validation.categoryMissing')
    minutesBetween(command.startAt, command.endAt)
    record.title = requireTitle(command.title)
    record.note = command.note.trim()
    record.categoryId = command.categoryId
    record.startAt = instant(command.startAt)
    record.endAt = instant(command.endAt)
    return { recordId: record.id }
  }
  if (command.type === 'deleteRecord') {
    requireCondition(workspace.records.some(item => item.id === command.recordId), 'validation.recordMissing')
    workspace.records = workspace.records.filter(item => item.id !== command.recordId)
    for (const plan of workspace.plans) for (const log of plan.logs) log.recordIds = log.recordIds.filter(id => id !== command.recordId)
    for (const todo of workspace.todos) todo.recordIds = todo.recordIds.filter(id => id !== command.recordId)
    return { recordId: command.recordId }
  }
  if (command.type === 'updateLog') {
    const plan = findPlan(workspace, command.planId)
    const log = plan.logs.find(item => item.id === command.logId)
    requireCondition(log, 'validation.logMissing')
    log.content = requireTitle(command.content)
    plan.updatedAt = context.now
    return { logId: log.id }
  }
  return undefined
}

