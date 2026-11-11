import type { Workspace, InstalledPackage } from './models'
import type { CoreCommand, WorkspaceCommand } from './commands'
import { requireCondition } from './errors'

const dataCommands = new Set([
  'createPlan', 'updatePlan', 'archivePlan', 'addNode', 'updateNode', 'deleteNode', 'setTaskCompletion', 'assignCategory',
  'recordAction', 'updateRecord', 'deleteRecord', 'updateLog', 'deleteLog', 'saveTodo', 'setTodoStatus', 'deleteTodo', 'saveCategory',
  'setTodoPinned', 'setTodoSubtask',
  'saveTimePlan', 'deleteTimePlan', 'setDateTimePlan', 'saveTimeRule', 'deleteTimeRule',
])
export function authorizedPackage(workspace: Workspace, identity: { kind: string; packageId: number; checksum: string }, capability: string): InstalledPackage {
  const entry = workspace.packages.find(item => item.kind === identity.kind && item.id === identity.packageId)
  requireCondition(entry && entry.status === 'enabled' && entry.checksum === identity.checksum && entry.permissions.includes(capability) && entry.grants.includes(capability), 'extensions.permissionDenied')
  return entry
}
export function unwrapExtensionCommand(workspace: Workspace, command: Extract<WorkspaceCommand, { type: 'extensionCommand' }>): CoreCommand {
  authorizedPackage(workspace, command, command.scope)
  const inner = command.command
  requireCondition(inner && typeof inner === 'object', 'extensions.permissionDenied')
  if (command.scope === 'app.data.write') requireCondition(dataCommands.has(inner.type), 'extensions.permissionDenied')
  else {
    requireCondition(inner.type === 'savePreferences', 'extensions.permissionDenied')
    const keys = Object.keys(inner.preferences)
    if (command.scope === 'app.theme') requireCondition(keys.length === 1 && keys[0] === 'themeId', 'extensions.permissionDenied')
    else requireCondition(keys.every(key => ['locale', 'fontId', 'timeZone', 'weekStartsOn'].includes(key)), 'extensions.permissionDenied')
  }
  return inner
}

