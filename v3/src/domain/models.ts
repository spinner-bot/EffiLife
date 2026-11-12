export type EntityId = string
export type Instant = string
export type NodeKind = 'section' | 'group' | 'task'
export type TodoStatus = 'pending' | 'in-progress' | 'completed' | 'archived' | 'cancelled'

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
  deletedAt?: Instant
  legacyCode?: string
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
  categoryId?: EntityId
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
  todoId?: EntityId
  timing: 'actual' | 'confirmed-reference'
  source: 'manual' | 'legacy-import' | 'archive'
  operationId?: string
}

export interface TodoSubtask { id: EntityId; title: string; completed: boolean; completedAt?: Instant }
export interface TodoRecurrence { frequency: 'day' | 'week' | 'month'; interval: number; anchorDay?: number }

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
  pinned?: boolean
  sortOrder?: number
  subtasks?: TodoSubtask[]
  recurrence?: TodoRecurrence
  deadlineWarningDays?: number
  previousOccurrenceId?: EntityId
  nextOccurrenceId?: EntityId
  relatedPlanId?: EntityId
  relatedTaskId?: EntityId
}

export interface HeaderClockPreferences {
  display: 'date' | 'time' | 'both'
  hourCycle: 12 | 24
  showPeriod: boolean
  align: 'center' | 'right'
}
export interface Preferences {
  headerClock?: HeaderClockPreferences
  appearance?: Record<string, import('./appearance').AppearanceOptions>
  locale: string
  themeId: number
  fontId: string
  timeZone: string
  weekStartsOn: number
}

export interface TimePlan {
  id: EntityId
  name: string
  mode: 'allocation' | 'partition'
  items: Array<{ categoryId: EntityId; minutes: number }>
  backgroundCategoryId?: EntityId
}

export interface TimeRule {
  id: EntityId
  kind: 'week' | 'month' | 'year' | 'month_week' | 'default'
  value: string
  planId: EntityId
}

export interface TimePlanning {
  plans: TimePlan[]
  rules: TimeRule[]
  overrides: Record<string, EntityId>
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
  checksum?: string
  installedAt?: Instant
  updatedAt?: Instant
}

export interface ExtensionAudit {
  id: string
  packageId: number
  kind: InstalledPackage['kind']
  action: 'install' | 'upgrade' | 'grants' | 'enable' | 'disable' | 'remove' | 'failure' | 'write'
  occurredAt: Instant
  capabilities: string[]
  detail?: string
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
  timePlanning?: TimePlanning
  extensionAudit?: ExtensionAudit[]
}

export interface CommandContext {
  now: Instant
  id: () => EntityId
}

