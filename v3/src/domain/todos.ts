import type { Todo, Workspace } from './models'
import { priorityScore } from './priority'
import { unionMinutes } from './time'

export type TodoSort = 'priority' | 'deadline' | 'created' | 'manual'
export function activeTodo(todo: Todo): boolean { return todo.status === 'pending' || todo.status === 'in-progress' }
export function sortTodos(workspace: Workspace, todos: readonly Todo[], now: string, sort: TodoSort = 'priority'): Todo[] {
  const score = (todo: Todo) => priorityScore(todo, workspace.categories.find(item => item.id === todo.categoryId)!, now)
  return [...todos].sort((a, b) => {
    const pinned = Number(Boolean(b.pinned)) - Number(Boolean(a.pinned))
    if (pinned) return pinned
    if (sort === 'deadline') {
      const difference = (a.deadline ? Date.parse(a.deadline) : Infinity) - (b.deadline ? Date.parse(b.deadline) : Infinity)
      if (difference && !Number.isNaN(difference)) return difference
    }
    if (sort === 'manual' && a.sortOrder !== b.sortOrder) return (a.sortOrder || 0) - (b.sortOrder || 0)
    if (sort === 'priority') { const difference = score(b) - score(a); if (difference) return difference }
    return Date.parse(b.createdAt) - Date.parse(a.createdAt) || a.id.localeCompare(b.id)
  })
}
export function todoMinutes(workspace: Workspace, todo: Todo): number {
  const records = workspace.records.filter(record => todo.recordIds.includes(record.id))
  return unionMinutes(records.map(record => [Date.parse(record.startAt), Date.parse(record.endAt)]))
}
export function matchesTodo(todo: Todo, search: string, categoryId = '', tag = ''): boolean {
  if (categoryId && todo.categoryId !== categoryId || tag && !todo.tags.includes(tag)) return false
  const text = [todo.title, todo.description, ...todo.tags, ...(todo.subtasks || []).map(item => item.title)].join(' ').toLocaleLowerCase()
  return search.trim().toLocaleLowerCase().split(/\s+/).every(word => text.includes(word))
}

