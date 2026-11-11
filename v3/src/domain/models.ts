export type EntityId = string
export type Instant = string
export type NodeKind = 'section' | 'group' | 'task'
export type TodoStatus = 'pending' | 'completed' | 'archived'

export interface Category {
  id: EntityId
  name: string
  labelKey?: string
  color: string
  icon: string
  difficulty: number
}

export interface PlanNode {
  id: EntityId
  parentId: EntityId | null
  kind: NodeKind
  title: string
  description: string
  order: number
  categoryId?: EntityId
  estimatedMinutes: number
  completedAt?: Instant
}

export interface TimingReference {
  startAt: Instant
  endAt: Instant
  minutes: number
  source: 'previous-observation'
  anchorId: EntityId
}

export interface ProgressLog {
  id: EntityId
  taskId?: EntityId
  occurredAt: Instant
  content: string
  kind: 'progress' | 'completion'
  recordIds: EntityId[]
  timingReference?: TimingReference
  timePrecision?: 'minute' | 'hour' | 'date'
}

export interface Plan {
  id: EntityId
  title: string
  description: string
  createdAt: Instant
  updatedAt: Instant
  archivedAt?: Instant
  nodes: PlanNode[]
  logs: ProgressLog[]
  legacy?: unknown
}

export interface TimeRecord {
  id: EntityId
  title: string
  note: string
  categoryId: EntityId
  startAt: Instant
  endAt: Instant
  planId?: EntityId
  taskId?: EntityId
  logId?: EntityId
  timing: 'actual' | 'confirmed-reference'
  source: 'manual' | 'legacy-import' | 'archive'
  operationId?: string
}

export interface Todo {
  id: EntityId
  title: string
  description: string
  categoryId: EntityId
  createdAt: Instant
  updatedAt: Instant
  startAt: Instant
  deadline?: Instant
  priorityRank: number
  urgent: boolean
  important: boolean
  estimatedMinutes: number
  status: TodoStatus
  completedAt?: Instant
  tags: string[]
  recordIds: EntityId[]
}

export interface Preferences {
  locale: string
  themeId: number
  fontId: string
  timeZone: string
  weekStartsOn: number
}

export interface OperationResult {
  entityId?: EntityId
  recordId?: EntityId
  logId?: EntityId
}

export interface OperationReceipt {
  fingerprint: string
  result: OperationResult
}

export interface InstalledPackage {
  id: number
  kind: 'theme' | 'resource' | 'function' | 'data'
  name: string
  author: string
  version: string
  source: 'builtin' | 'local'
  status: 'enabled' | 'disabled' | 'broken'
  permissions: string[]
  grants: string[]
  manifest: Record<string, unknown>
  payload: Record<string, string>
}

export interface Workspace {
  schemaVersion: 1
  productVersion: string
  revision: number
  updatedAt: Instant
  categories: Category[]
  plans: Plan[]
  records: TimeRecord[]
  todos: Todo[]
  preferences: Preferences
  receipts: Record<string, OperationReceipt>
  packages: InstalledPackage[]
  packageTombstones: Array<{ kind: InstalledPackage['kind']; id: number }>
  legacy?: { importedAt: Instant; source: unknown }
}

export interface CommandContext {
  now: Instant
  id: () => EntityId
}

