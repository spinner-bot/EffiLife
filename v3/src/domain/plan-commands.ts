import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { findPlan, findNode, descendants } from './plans'
import { requireCondition, requireTitle } from './errors'

export function applyPlanCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (command.type === 'createPlan') {
    const id = context.id()
    workspace.plans.push({ id, title: requireTitle(command.title), description: command.description?.trim() || '', createdAt: context.now, updatedAt: context.now, nodes: [], logs: [] })
    return { entityId: id }
  }
  if (!['updatePlan', 'archivePlan', 'addNode', 'updateNode', 'deleteNode', 'setTaskCompletion', 'assignCategory'].includes(command.type)) return undefined
  requireCondition('planId' in command && command.planId, 'validation.planMissing')
  const plan = findPlan(workspace, command.planId)
  plan.updatedAt = context.now
  switch (command.type) {
    case 'updatePlan':
      plan.title = requireTitle(command.title)
      plan.description = command.description.trim()
      break
    case 'archivePlan':
      plan.archivedAt = command.archived ? context.now : undefined
      break
    case 'addNode': {
      requireCondition(!plan.archivedAt, 'validation.planArchived')
      if (command.parentId) requireCondition(findNode(plan, command.parentId).kind !== 'task', 'validation.invalidParent')
      if (command.categoryId) requireCondition(workspace.categories.some(category => category.id === command.categoryId), 'validation.categoryMissing')
      const estimate = command.estimatedMinutes ?? 0
      requireCondition(Number.isFinite(estimate) && estimate >= 0, 'validation.invalidDuration')
      const id = context.id()
      plan.nodes.push({ id, parentId: command.parentId, kind: command.kind, title: requireTitle(command.title), description: command.description?.trim() || '', order: plan.nodes.length, estimatedMinutes: estimate, categoryId: command.categoryId })
      return { entityId: id }
    }
    case 'updateNode': {
      const node = findNode(plan, command.nodeId)
      requireCondition(Number.isFinite(command.estimatedMinutes) && command.estimatedMinutes >= 0, 'validation.invalidDuration')
      node.title = requireTitle(command.title)
      node.description = command.description.trim()
      node.estimatedMinutes = command.estimatedMinutes
      break
    }
    case 'deleteNode': {
      const target = findNode(plan, command.nodeId)
      const removed = new Set([target.id, ...descendants(plan, target.id).map(node => node.id)])
      requireCondition(!plan.logs.some(log => log.taskId && removed.has(log.taskId)) && !workspace.records.some(record => record.planId === plan.id && record.taskId && removed.has(record.taskId)), 'validation.taskHasHistory')
      plan.nodes = plan.nodes.filter(node => !removed.has(node.id))
      for (const todo of workspace.todos) {
        if (todo.relatedPlanId === plan.id && todo.relatedTaskId && removed.has(todo.relatedTaskId)) {
          todo.relatedTaskId = undefined
          todo.updatedAt = context.now
        }
      }
      break
    }
    case 'setTaskCompletion': {
      const task = findNode(plan, command.taskId)
      requireCondition(task.kind === 'task', 'validation.taskRequired')
      task.completedAt = command.completed ? context.now : undefined
      break
    }
    case 'assignCategory': {
      requireCondition(workspace.categories.some(category => category.id === command.categoryId), 'validation.categoryMissing')
      const parent = command.nodeId === null ? plan : findNode(plan, command.nodeId)
      parent.categoryId = command.categoryId
      if (command.overwrite) for (const child of command.nodeId === null ? plan.nodes : descendants(plan, parent.id)) child.categoryId = command.categoryId
      break
    }
  }
  return { entityId: plan.id }
}

