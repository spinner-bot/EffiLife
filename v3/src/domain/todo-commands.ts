import type { CommandContext, OperationResult, Workspace } from './models'
import type { WorkspaceCommand } from './commands'
import { requireCondition, requireTitle } from './errors'
import { instant } from './time'
import { assertRecurrence, nextTodoOccurrence } from './todo-recurrence'

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
    if (command.recurrence) assertRecurrence(command.recurrence)
    const warning = command.deadlineWarningDays ?? current?.deadlineWarningDays ?? 3
    requireCondition(Number.isSafeInteger(warning) && warning >= 0, 'validation.invalidDuration')
    const sortOrder = command.sortOrder ?? current?.sortOrder ?? 0
    requireCondition(Number.isFinite(sortOrder), 'validation.invalidPriority')
    const subtasks = command.subtasks?.map(item => {
      requireCondition(typeof item.id === 'string' && item.id.trim() && typeof item.completed === 'boolean', 'validation.invalidSubtasks')
      const old = current?.subtasks?.find(subtask => subtask.id === item.id)
      return { id: item.id, title: requireTitle(item.title), completed: item.completed, completedAt: item.completed ? old?.completed ? old.completedAt : context.now : undefined }
    }) ?? current?.subtasks ?? []
    requireCondition(new Set(subtasks.map(item => item.id)).size === subtasks.length, 'validation.invalidSubtasks')
    const id = current?.id || context.id()
    const value = {
      id, title: requireTitle(command.title), description: (command.description ?? current?.description ?? '').trim(),
      categoryId, createdAt: current?.createdAt || context.now, updatedAt: context.now, startAt: current?.startAt || context.now,
      deadline: command.deadline === undefined ? current?.deadline : command.deadline ? instant(command.deadline) : undefined, priorityRank,
      urgent: command.urgent ?? current?.urgent ?? false, important: command.important ?? current?.important ?? false,
      estimatedMinutes, status: current?.status || 'pending' as const, completedAt: current?.completedAt,
      tags: [...new Set((command.tags ?? current?.tags ?? []).map(tag => tag.trim()).filter(Boolean))],
      recordIds: current?.recordIds || [],
      pinned: command.pinned ?? current?.pinned ?? false, sortOrder, subtasks,
      recurrence: command.recurrence === undefined ? current?.recurrence : command.recurrence || undefined,
      deadlineWarningDays: warning,
    }
    if (current) Object.assign(current, value)
    else workspace.todos.push(value)
    return { entityId: id }
  }
  if (command.type === 'setTodoStatus') {
    const todo = workspace.todos.find(item => item.id === command.todoId)
    requireCondition(todo, 'validation.todoMissing')
    requireCondition(['pending', 'in-progress', 'completed', 'archived', 'cancelled'].includes(command.status), 'validation.todoMissing')
    if (command.status === 'completed' && todo.status !== 'completed' && todo.recurrence && !todo.nextOccurrenceId) {
      const next = nextTodoOccurrence(todo, context.now, workspace.preferences.timeZone)!
      const nextId = context.id()
      const clone = structuredClone(todo)
      workspace.todos.push({ ...clone, id: nextId, createdAt: context.now, updatedAt: context.now, startAt: context.now, deadline: next.at, recurrence: next.recurrence, status: 'pending', completedAt: undefined, recordIds: [], previousOccurrenceId: todo.id, nextOccurrenceId: undefined, subtasks: clone.subtasks?.map(item => ({ id: context.id(), title: item.title, completed: false })) })
      todo.nextOccurrenceId = nextId
    }
    todo.status = command.status
    todo.completedAt = command.status === 'completed' ? context.now : undefined
    todo.updatedAt = context.now
    return { entityId: todo.id }
  }
  if (command.type === 'deleteTodo') {
    requireCondition(workspace.todos.some(todo => todo.id === command.todoId), 'validation.todoMissing')
    workspace.todos = workspace.todos.filter(todo => todo.id !== command.todoId)
    for (const todo of workspace.todos) {
      if (todo.previousOccurrenceId === command.todoId) todo.previousOccurrenceId = undefined
      if (todo.nextOccurrenceId === command.todoId) todo.nextOccurrenceId = undefined
    }
    return { entityId: command.todoId }
  }
  if (command.type === 'setTodoPinned' || command.type === 'setTodoSubtask') {
    const todo = workspace.todos.find(item => item.id === command.todoId)
    requireCondition(todo, 'validation.todoMissing')
    if (command.type === 'setTodoPinned') todo.pinned = Boolean(command.pinned)
    else {
      const item = todo.subtasks?.find(item => item.id === command.subtaskId)
      requireCondition(item, 'validation.subtaskMissing')
      item.completed = Boolean(command.completed)
      item.completedAt = item.completed ? context.now : undefined
    }
    todo.updatedAt = context.now
    return { entityId: todo.id }
  }
  return undefined
}

