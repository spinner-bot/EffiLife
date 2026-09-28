import { deleteRaw, get, getRawAll, putRaw, set, STORE_NAMES } from '@/storage'
import { translate } from '@/i18n'
import { notifyWorkspaceChanged } from './workspaceEvents'

export type TodoStatus = 'pending' | 'in-progress' | 'completed' | 'archived' | 'cancelled'
export type TodoPriority = 'urgent-important' | 'important' | 'urgent' | 'normal'
export type TodoRecurrence = 'none' | 'daily' | 'weekly' | 'monthly' | 'custom'

export interface TodoSubtask {
  id: string
  title: string
  completed: boolean
  completed_at?: string
}

export interface TodoCategory {
  id: string
  name: string
  color: string
  icon: string
  ascii_icon?: string
  pinned?: boolean
  created_at: string
  difficulty: number
}

export interface TodoSettings {
  updateFrequency: number
  expandCount: number
}

export const DEFAULT_TODO_SETTINGS: TodoSettings = {
  updateFrequency: 60_000,
  expandCount: 5,
}

const TODO_SETTINGS_KEY = 'todo_settings'

function normalizeTodoSettings(value: Partial<TodoSettings> | null | undefined): TodoSettings {
  const allowedFrequencies = [5_000, 10_000, 15_000, 30_000, 60_000]
  const frequency = Number(value?.updateFrequency)
  const expandCount = Number(value?.expandCount)
  return {
    updateFrequency: allowedFrequencies.includes(frequency) ? frequency : DEFAULT_TODO_SETTINGS.updateFrequency,
    expandCount: Number.isFinite(expandCount) ? Math.max(1, Math.min(20, Math.trunc(expandCount))) : DEFAULT_TODO_SETTINGS.expandCount,
  }
}

export const DEFAULT_TODO_CATEGORIES: TodoCategory[] = [
  { id: 'default', name: '默认', color: '#6366f1', icon: 'circle', created_at: '2026-01-01T00:00:00.000Z', difficulty: 5 },
]

const LEGACY_TODOS_KEY = 'to-dos-data'
const LEGACY_MIGRATION_MARKER = 'effilife_todos_legacy_migrated_v1'
let legacyMigrationAttempted = false

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
  related_time_record_ids?: string[]
}

export interface LegacyTodoImportResult {
  migrated: number
  categories: number
  skipped: number
  warnings: number
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

function makeSubtaskId(): string {
  const suffix = typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `SUB-${suffix.toUpperCase()}`
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
    // Keep the algorithm's start boundary explicit for newly created tasks.
    // Legacy imports without it still fall back to their creation timestamp.
    start_time: todo.start_time || todo.created_at || timestamp,
    estimated_time: todo.estimated_time,
    related_time_record_ids: todo.related_time_record_ids,
  }
}

/**
 * Normalize a record coming from an archive or another module before it is
 * written to the local todo store. Invalid records are rejected so imports do
 * not create silently corrupted tasks.
 */
export function normalizeImportedTodo(value: unknown): UnifiedTodo | null {
  if (!value || typeof value !== 'object') return null
  const candidate = value as Partial<UnifiedTodo>
  if (typeof candidate.title !== 'string' || !candidate.title.trim()) return null
  if (candidate.id !== undefined && typeof candidate.id !== 'string') return null
  if (candidate.related_plan_id !== undefined && typeof candidate.related_plan_id !== 'string') return null
  if (candidate.related_plan_task_id !== undefined && typeof candidate.related_plan_task_id !== 'string') return null
  if (candidate.related_time_record_ids !== undefined && (
    !Array.isArray(candidate.related_time_record_ids)
    || candidate.related_time_record_ids.some((id) => typeof id !== 'string')
  )) return null
  return normalize(candidate as Partial<UnifiedTodo> & Pick<UnifiedTodo, 'title'>)
}

export function normalizeImportedCategory(value: unknown): TodoCategory | null {
  if (!value || typeof value !== 'object') return null
  const candidate = value as Partial<TodoCategory>
  if (typeof candidate.id !== 'string' || !candidate.id.trim()) return null
  if (typeof candidate.name !== 'string' || !candidate.name.trim()) return null
  if (typeof candidate.color !== 'string' || !candidate.color.trim()) return null
  return {
    id: candidate.id,
    name: candidate.name.trim(),
    color: candidate.color,
    icon: typeof candidate.icon === 'string' && candidate.icon ? candidate.icon : 'circle',
    ascii_icon: typeof candidate.ascii_icon === 'string' ? candidate.ascii_icon : undefined,
    pinned: candidate.pinned === true,
    created_at: typeof candidate.created_at === 'string' && candidate.created_at
      ? candidate.created_at
      : new Date().toISOString(),
    difficulty: typeof candidate.difficulty === 'number' && Number.isFinite(candidate.difficulty)
      ? Math.max(0, Math.min(10, candidate.difficulty))
      : 5,
  }
}

function makeCategoryId(): string {
  const suffix = typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID().slice(0, 8)
    : Math.random().toString(36).slice(2, 10)
  return `CAT-${suffix.toUpperCase()}`
}

export const TodoCategoryService = {
  async list(): Promise<TodoCategory[]> {
    const categories = await getRawAll<TodoCategory>(STORE_NAMES.TODO_CATEGORIES)
    return categories.sort((a, b) => a.name.localeCompare(b.name))
  },

  async ensureDefaults(todos: UnifiedTodo[] = []): Promise<TodoCategory[]> {
    const existing = await this.list()
    const byId = new Map(existing.map((category) => [category.id, category]))
    for (const category of DEFAULT_TODO_CATEGORIES) {
      if (!byId.has(category.id)) {
        await putRaw(STORE_NAMES.TODO_CATEGORIES, category)
        byId.set(category.id, category)
      }
    }
    for (const todo of todos) {
      if (!todo.category || byId.has(todo.category)) continue
      const inferred: TodoCategory = {
        id: todo.category,
        name: todo.category,
        color: '#64748b',
        icon: 'circle',
        created_at: new Date().toISOString(),
        difficulty: 5,
      }
      await putRaw(STORE_NAMES.TODO_CATEGORIES, inferred)
      byId.set(inferred.id, inferred)
    }
    return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name))
  },

  async create(input: Pick<TodoCategory, 'name' | 'color'> & Partial<Pick<TodoCategory, 'icon' | 'ascii_icon' | 'pinned' | 'difficulty'>>): Promise<TodoCategory> {
    const category = normalizeImportedCategory({
      ...input,
      id: makeCategoryId(),
      created_at: new Date().toISOString(),
    })
    if (!category) throw new Error(translate('tasks.error.categoryInvalid'))
    await putRaw(STORE_NAMES.TODO_CATEGORIES, category)
    notifyWorkspaceChanged('todos')
    return category
  },

  async update(id: string, patch: Partial<Pick<TodoCategory, 'name' | 'color' | 'icon' | 'ascii_icon' | 'pinned' | 'difficulty'>>): Promise<TodoCategory> {
    const categories = await this.list()
    const current = categories.find((category) => category.id === id)
    if (!current) throw new Error(translate('tasks.error.categoryMissing'))
    const next = normalizeImportedCategory({ ...current, ...patch })
    if (!next) throw new Error(translate('tasks.error.categoryInvalid'))
    await putRaw(STORE_NAMES.TODO_CATEGORIES, next)
    notifyWorkspaceChanged('todos')
    return next
  },

  async remove(id: string): Promise<void> {
    if (id === 'default') throw new Error(translate('tasks.error.defaultCategory'))
    await deleteRaw(STORE_NAMES.TODO_CATEGORIES, id)
    notifyWorkspaceChanged('todos')
  },
}

export const TodoSettingsService = {
  async get(): Promise<TodoSettings> {
    try {
      return normalizeTodoSettings(await get<Partial<TodoSettings>>(STORE_NAMES.CONFIG, TODO_SETTINGS_KEY))
    } catch {
      return { ...DEFAULT_TODO_SETTINGS }
    }
  },

  async save(value: Partial<TodoSettings>): Promise<TodoSettings> {
    const settings = normalizeTodoSettings(value)
    await set(STORE_NAMES.CONFIG, TODO_SETTINGS_KEY, settings)
    notifyWorkspaceChanged('settings')
    return settings
  },
}

export const TodoService = {
  async migrateLegacyLocalStorage(): Promise<{ migrated: number; categories: number; skipped: number }> {
    if (legacyMigrationAttempted) return { migrated: 0, categories: 0, skipped: 0 }
    legacyMigrationAttempted = true
    if (localStorage.getItem(LEGACY_MIGRATION_MARKER)) return { migrated: 0, categories: 0, skipped: 0 }

    const source = localStorage.getItem(LEGACY_TODOS_KEY)
    if (!source) {
      localStorage.setItem(LEGACY_MIGRATION_MARKER, new Date().toISOString())
      return { migrated: 0, categories: 0, skipped: 0 }
    }

    try {
      const payload = JSON.parse(source) as { todos?: unknown[]; categories?: unknown[] }
      const existingTodos = await this.list()
      const existingIds = new Set(existingTodos.map((todo) => todo.id))
      let migrated = 0
      let skipped = 0
      for (const raw of Array.isArray(payload.todos) ? payload.todos : []) {
        const todo = normalizeImportedTodo(raw)
        if (!todo || existingIds.has(todo.id)) {
          skipped += 1
          continue
        }
        await putRaw(STORE_NAMES.TODOS, todo)
        existingIds.add(todo.id)
        migrated += 1
      }

      const existingCategories = await TodoCategoryService.list()
      const categoryIds = new Set(existingCategories.map((category) => category.id))
      let categories = 0
      for (const raw of Array.isArray(payload.categories) ? payload.categories : []) {
        const category = normalizeImportedCategory(raw)
        if (!category || categoryIds.has(category.id)) continue
        await putRaw(STORE_NAMES.TODO_CATEGORIES, category)
        categoryIds.add(category.id)
        categories += 1
      }
      await TodoCategoryService.ensureDefaults([...existingTodos, ...(Array.isArray(payload.todos) ? payload.todos.map(normalizeImportedTodo).filter((todo): todo is UnifiedTodo => todo !== null) : [])])
      localStorage.setItem(LEGACY_MIGRATION_MARKER, new Date().toISOString())
      return { migrated, categories, skipped }
    } catch {
      legacyMigrationAttempted = false
      return { migrated: 0, categories: 0, skipped: 0 }
    }
  },

  async list(): Promise<UnifiedTodo[]> {
    const todos = await getRawAll<UnifiedTodo>(STORE_NAMES.TODOS)
    return todos.sort((a, b) => {
      if (Boolean(b.pinned) !== Boolean(a.pinned)) return Number(Boolean(b.pinned)) - Number(Boolean(a.pinned))
      return b.updated_at.localeCompare(a.updated_at)
    })
  },

  async create(input: Partial<UnifiedTodo> & Pick<UnifiedTodo, 'title'>): Promise<UnifiedTodo> {
    const todo = normalize(input)
    if (!todo.title) throw new Error(translate('tasks.error.titleRequired'))
    await putRaw(STORE_NAMES.TODOS, todo)
    notifyWorkspaceChanged('todos')
    return todo
  },

  async update(id: string, patch: Partial<UnifiedTodo>): Promise<UnifiedTodo> {
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error(translate('tasks.error.taskMissing'))
    const next = normalize({ ...current, ...patch, id: current.id, created_at: current.created_at, title: patch.title ?? current.title })
    await putRaw(STORE_NAMES.TODOS, next)
    notifyWorkspaceChanged('todos')
    return next
  },

  async complete(id: string): Promise<UnifiedTodo> {
    return this.update(id, { status: 'completed', completed_at: now() })
  },

  async addSubtask(id: string, title: string): Promise<UnifiedTodo> {
    const cleanTitle = title.trim()
    if (!cleanTitle) throw new Error(translate('tasks.error.subtaskTitleRequired'))
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error(translate('tasks.error.taskMissing'))
    return this.update(id, {
      subtasks: [...current.subtasks, { id: makeSubtaskId(), title: cleanTitle, completed: false }],
    })
  },

  async toggleSubtask(id: string, subtaskId: string): Promise<UnifiedTodo> {
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error(translate('tasks.error.taskMissing'))
    let found = false
    const subtasks = current.subtasks.map((subtask) => {
      if (subtask.id !== subtaskId) return subtask
      found = true
      const completed = !subtask.completed
      return { ...subtask, completed, completed_at: completed ? now() : undefined }
    })
    if (!found) throw new Error(translate('tasks.error.subtaskMissing'))
    return this.update(id, { subtasks })
  },

  async removeSubtask(id: string, subtaskId: string): Promise<UnifiedTodo> {
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error(translate('tasks.error.taskMissing'))
    const subtasks = current.subtasks.filter((subtask) => subtask.id !== subtaskId)
    if (subtasks.length === current.subtasks.length) throw new Error(translate('tasks.error.subtaskMissing'))
    return this.update(id, { subtasks })
  },

  async remove(id: string): Promise<void> {
    await deleteRaw(STORE_NAMES.TODOS, id)
    notifyWorkspaceChanged('todos')
  },

  async trackTime(id: string, minutes: number, timeRecordId?: string | string[]): Promise<UnifiedTodo> {
    const todos = await this.list()
    const current = todos.find((todo) => todo.id === id)
    if (!current) throw new Error(translate('tasks.error.taskMissing'))
    if (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440) {
      throw new Error(translate('tasks.error.invalidMinutes'))
    }
    const recordIds = Array.isArray(timeRecordId)
      ? timeRecordId.filter(Boolean)
      : timeRecordId ? [timeRecordId] : []
    return this.update(id, {
      time_spent: (current.time_spent || 0) + minutes,
      related_time_record_ids: recordIds.length > 0
        ? [...(current.related_time_record_ids || []), ...recordIds]
        : current.related_time_record_ids,
    })
  },
}

/** Import a to-dos JSON export without replacing current unified data. */
export async function importLegacyTodoPayload(source: unknown): Promise<LegacyTodoImportResult> {
  let payload: unknown = source
  if (typeof source === 'string') {
    try {
      payload = JSON.parse(source)
    } catch {
      throw new Error(translate('tasks.legacyTodoInvalidJson'))
    }
  }
  const rawTodos = Array.isArray(payload) ? payload : (payload && typeof payload === 'object' ? (payload as { todos?: unknown[] }).todos : undefined)
  const rawCategories = payload && typeof payload === 'object' && !Array.isArray(payload)
    ? (payload as { categories?: unknown[] }).categories
    : []
  if (!Array.isArray(rawTodos)) throw new Error(translate('tasks.legacyTodoMissingTodos'))

  const normalizedTodos: UnifiedTodo[] = []
  let warnings = 0
  for (const raw of rawTodos) {
    const todo = normalizeImportedTodo(raw)
    if (!todo) {
      warnings += 1
      continue
    }
    normalizedTodos.push(todo)
  }
  const normalizedCategories = Array.isArray(rawCategories)
    ? rawCategories.map(normalizeImportedCategory).filter((category): category is TodoCategory => category !== null)
    : []
  const existingTodos = await TodoService.list()
  const existingIds = new Set(existingTodos.map((todo) => todo.id))
  let migrated = 0
  let skipped = 0
  for (const todo of normalizedTodos) {
    if (existingIds.has(todo.id)) {
      skipped += 1
      continue
    }
    await putRaw(STORE_NAMES.TODOS, todo)
    existingIds.add(todo.id)
    migrated += 1
  }

  const existingCategories = await TodoCategoryService.list()
  const categoryIds = new Set(existingCategories.map((category) => category.id))
  let categories = 0
  for (const category of normalizedCategories) {
    if (categoryIds.has(category.id)) continue
    await putRaw(STORE_NAMES.TODO_CATEGORIES, category)
    categoryIds.add(category.id)
    categories += 1
  }
  await TodoCategoryService.ensureDefaults([...existingTodos, ...normalizedTodos])
  if (migrated > 0 || categories > 0) notifyWorkspaceChanged('todos')
  return { migrated, categories, skipped, warnings }
}
