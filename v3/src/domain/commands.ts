import type { Instant, NodeKind, Preferences, Todo, TodoStatus, TodoRecurrence, TimePlan, TimeRule } from './models'
import type { PackageCandidate } from '../extensions/manifest'
import type { Capability } from '../extensions/capabilities'

export type CoreCommand =
  | { type: 'createPlan'; title: string; description?: string }
  | { type: 'updatePlan'; planId: string; title: string; description: string }
  | { type: 'archivePlan'; planId: string; archived: boolean }
  | { type: 'addNode'; planId: string; parentId: string | null; kind: NodeKind; title: string; description?: string; estimatedMinutes?: number; categoryId?: string }
  | { type: 'updateNode'; planId: string; nodeId: string; title: string; description: string; estimatedMinutes: number }
  | { type: 'deleteNode'; planId: string; nodeId: string }
  | { type: 'setTaskCompletion'; planId: string; taskId: string; completed: boolean }
  | { type: 'assignCategory'; planId: string; nodeId: string | null; categoryId: string; overwrite: boolean }
  | { type: 'recordAction'; title?: string; content: string; occurredAt?: Instant; planId?: string; taskId?: string; todoId?: string; completeTodo?: boolean; startAt?: Instant; endAt?: Instant; categoryId?: string; completeTask?: boolean; timing?: 'actual' | 'confirmed-reference' }
  | { type: 'updateRecord'; recordId: string; title: string; note: string; categoryId: string; startAt: Instant; endAt: Instant }
  | { type: 'deleteRecord'; recordId: string }
  | { type: 'updateLog'; planId: string; logId: string; content: string }
  | { type: 'deleteLog'; planId: string; logId: string }
  | { type: 'saveTodo'; todoId?: string; title: string; description?: string; categoryId?: string; deadline?: Instant | null; priorityRank?: number; urgent?: boolean; important?: boolean; estimatedMinutes?: number; tags?: string[]; pinned?: boolean; sortOrder?: number; subtasks?: Array<{ id: string; title: string; completed: boolean }>; recurrence?: TodoRecurrence | null; deadlineWarningDays?: number }
  | { type: 'setTodoPinned'; todoId: string; pinned: boolean }
  | { type: 'setTodoSubtask'; todoId: string; subtaskId: string; completed: boolean }
  | { type: 'setTodoStatus'; todoId: string; status: TodoStatus; occurredAt?: Instant }
  | { type: 'deleteTodo'; todoId: string }
  | { type: 'savePreferences'; preferences: Partial<Preferences> }
  | { type: 'saveCategory'; categoryId?: string; name?: string; color: string; difficulty: number; icon?: string }
  | { type: 'saveTimePlan'; timePlanId?: string; name: string; mode: TimePlan['mode']; items: TimePlan['items']; backgroundCategoryId?: string; useForDate?: string; makeDefault?: boolean }
  | { type: 'deleteTimePlan'; timePlanId: string }
  | { type: 'setDateTimePlan'; date: string; timePlanId: string | null }
  | { type: 'saveTimeRule'; ruleId?: string; kind: TimeRule['kind']; value: string; timePlanId: string }
  | { type: 'deleteTimeRule'; ruleId: string }
  | { type: 'installPackage'; candidate: PackageCandidate; updateId?: number; grants?: Capability[] }
  | { type: 'setPackageGrants'; kind: 'theme' | 'resource' | 'function'; packageId: number; grants: Capability[] }
  | { type: 'setPackageStatus'; kind: 'theme' | 'resource' | 'function'; packageId: number; enabled: boolean }
  | { type: 'removePackage'; kind: 'theme' | 'resource' | 'function'; packageId: number }
  | { type: 'packageRuntimeFailure'; kind: 'theme' | 'function'; packageId: number; checksum: string; detail: string }
  | { type: 'recoverAppearance' }

export type WorkspaceCommand = CoreCommand | {
  type: 'extensionCommand'
  kind: 'theme' | 'function'
  packageId: number
  checksum: string
  scope: 'app.data.write' | 'app.settings.write' | 'app.theme'
  command: CoreCommand
}

export interface CommandEnvelope {
  operationId: string
  command: WorkspaceCommand
}

export type TodoEdit = Partial<Pick<Todo, 'description' | 'deadline' | 'priorityRank' | 'urgent' | 'important' | 'estimatedMinutes' | 'tags'>>

