import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { requireCondition, requireTitle } from './errors'
import { instant } from './time'

export function applyTodoCommand(workspace: Workspace, command: WorkspaceCommand, context: CommandContext): OperationResult | undefined {
  if (command.type === 'saveTodo') {
    const current = command.todoId ? workspace.todos.find(todo => todo.id === command.todoId) : undefined
    requireCondition(!command.todoId || current, 'validation.todoMissing')
    const categoryId = command.categoryId || current?.categoryId || 'life'
    requireCondition(workspace.categories.some(category => category.id === categoryId), 'validation.categoryMissing')
    const priorityRank = command.priorityRank ?? current?.priorityRank ?? 5
    const estimatedMinutes = command.estimatedMinutes ?? current?.estimatedMinutes ?? 0
    requireCondition(Number.isSafeInteger(priorityRank) && priorityRank >= 0, 'validation.invalidPriority')
    requireCondition(Number.isFinite(estimatedMinutes) && estimatedMinutes >= 0, 'validation.invalidDuration')
    const id = current?.id || context.id()
    const value = {
      id, title: requireTitle(command.title), description: (command.description ?? current?.description ?? '').trim(),
      categoryId, createdAt: current?.createdAt || context.now, updatedAt: context.now, startAt: current?.startAt || context.now,
      deadline: command.deadline ? instant(command.deadline) : undefined, priorityRank,
      urgent: command.urgent ?? current?.urgent ?? false, important: command.important ?? current?.important ?? false,
      estimatedMinutes, status: current?.status || 'pending' as const, completedAt: current?.completedAt,
      tags: [...new Set((command.tags ?? current?.tags ?? []).map(tag => tag.trim()).filter(Boolean))],
      recordIds: current?.recordIds || [],
    }
    if (current) Object.assign(current, value)
    else workspace.todos.push(value)
    return { entityId: id }
  }
  if (command.type === 'setTodoStatus') {
    const todo = workspace.todos.find(item => item.id === command.todoId)
    requireCondition(todo, 'validation.todoMissing')
    todo.status = command.status
    todo.completedAt = command.status === 'completed' ? context.now : undefined
    todo.updatedAt = context.now
    return { entityId: todo.id }
  }
  if (command.type === 'deleteTodo') {
    requireCondition(workspace.todos.some(todo => todo.id === command.todoId), 'validation.todoMissing')
    workspace.todos = workspace.todos.filter(todo => todo.id !== command.todoId)
    return { entityId: command.todoId }
  }
  return undefined
}

