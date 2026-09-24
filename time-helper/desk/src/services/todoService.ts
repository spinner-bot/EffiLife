import { deleteRaw, getRawAll, putRaw, STORE_NAMES } from '@/storage'

export type TodoStatus = 'pending' | 'in-progress' | 'completed' | 'archived' | 'cancelled'
export type TodoPriority = 'urgent-important' | 'important' | 'urgent' | 'normal'
export type TodoRecurrence = 'none' | 'daily' | 'weekly' | 'monthly' | 'custom'

export interface TodoSubtask {
  id: string
  title: string
  completed: boolean
  completed_at?: string
}

export interface UnifiedTodo {
  id: string
  title: string
  description?: string
  created_at: string
  updated_at: string
  priority: TodoPriority
  category: string
  status: TodoStatus
  deadline?: string
  completed_at?: string
  tags: string[]
  subtasks: TodoSubtask[]
  related_plan_id?: string
  related_plan_task_id?: string
  time_estimate?: number
  time_spent?: number
  notes?: string
  recurrence: TodoRecurrence
  deadline_warning_days: number
  sort_order: number
  pinned?: boolean
  priority_rank?: number
  urgent?: boolean
  important?: boolean
  start_time?: string
  estimated_time?: number
}

function now(): string {
  return new Date().toISOString()
}

function makeId(): string {
  const stamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const suffix = typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `TODO-${stamp}-${suffix.toUpperCase()}`
}

function normalize(todo: Partial<UnifiedTodo> & Pick<UnifiedTodo, 'title'>): UnifiedTodo {
  const timestamp = now()
  return {
    id: todo.id || makeId(),
    title: todo.title.trim(),
    description: todo.description?.trim() || undefined,
    created_at: todo.created_at || timestamp,
    updated_at: timestamp,
    priority: todo.priority || 'normal',
    category: todo.category || 'default',
    status: todo.status || 'pending',
    deadline: todo.deadline,
    completed_at: todo.completed_at,
    tags: todo.tags || [],
    subtasks: todo.subtasks || [],
    related_plan_id: todo.related_plan_id,
    related_plan_task_id: todo.related_plan_task_id,
    time_estimate: todo.time_estimate,
    time_spent: todo.time_spent,
    notes: todo.notes,
    recurrence: todo.recurrence || 'none',
    deadline_warning_days: todo.deadline_warning_days ?? 3,
    sort_order: todo.sort_order ?? 0,
    pinned: todo.pinned || false,
    priority_rank: todo.priority_rank,
    urgent: todo.urgent,
    important: todo.important,
    start_time: todo.start_time,
    estimated_time: todo.estimated_time,
  }
}

export const TodoService = {
  async list(): Promise<UnifiedTodo[]> {
    const todos = await getRawAll<UnifiedTodo>(STORE_NAMES.TODOS)
    return todos.sort((a, b) => {
      if (Boolean(b.pinned) !== Boolean(a.pinned)) return Number(Boolean(b.pinned)) - Number(Boolean(a.pinned))
      return b.updated_at.localeCompare(a.updated_at)
    })
  },

  async create(input: Partial<UnifiedTodo> & Pick<UnifiedTodo, 'title'>): Promise<UnifiedTodo> {
    const todo = normalize(input)
    if (!todo.title) throw new Error('任务标题不能为空')
    await putRaw(STORE_NAMES.TODOS, todo)
    return todo
  },

  async update(id: string, patch: Partial<UnifiedTodo>): Promise<UnifiedTodo> {
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error('任务不存在')
    const next = normalize({ ...current, ...patch, id: current.id, created_at: current.created_at, title: patch.title ?? current.title })
    await putRaw(STORE_NAMES.TODOS, next)
    return next
  },

  async complete(id: string): Promise<UnifiedTodo> {
    return this.update(id, { status: 'completed', completed_at: now() })
  },

  async remove(id: string): Promise<void> {
    await deleteRaw(STORE_NAMES.TODOS, id)
  },
}
