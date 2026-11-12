import type { CommandContext, OperationResult, Workspace } from './models'
import type { CommandEnvelope } from './commands'
import { applyPlanCommand } from './plan-commands'
import { applyRecordCommand } from './record-commands'
import { applyTodoCommand } from './todo-commands'
import { applyTimePlanCommand } from './time-plan-commands'
import { applyPackageCommand } from './package-commands'
import { requireCondition, requireTitle, DomainError } from './errors'
import { assertOptionalPreferences } from './preferences'
import { instant } from './time'
import { unwrapExtensionCommand } from './extension-access'

function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical)
  if (value && typeof value === 'object') return Object.fromEntries(
    Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, canonical(item)]),
  )
  return value
}

export function execute(
  original: Workspace, envelope: CommandEnvelope, context: CommandContext,
): { workspace: Workspace; result: OperationResult } {
  requireCondition(/^[a-zA-Z0-9][a-zA-Z0-9:_-]{0,199}$/.test(envelope.operationId), 'validation.operationId')
  const fingerprint = JSON.stringify(canonical(envelope.command))
  const previous = Object.hasOwn(original.receipts, envelope.operationId) ? original.receipts[envelope.operationId] : undefined
  if (previous) {
    requireCondition(previous.fingerprint === fingerprint, 'validation.operationConflict')
    return { workspace: original, result: structuredClone(previous.result) }
  }
  const workspace = structuredClone(original)
  const normalizedContext = { ...context, now: instant(context.now) }
  const extension = envelope.command.type === 'extensionCommand' ? envelope.command : undefined
  const command = extension ? unwrapExtensionCommand(workspace, extension) : envelope.command
  let result = applyPlanCommand(workspace, command, normalizedContext)
    ?? applyRecordCommand(workspace, command, normalizedContext)
    ?? applyTodoCommand(workspace, command, normalizedContext)
    ?? applyTimePlanCommand(workspace, command, normalizedContext)
    ?? applyPackageCommand(workspace, command, normalizedContext)
  if (command.type === 'savePreferences') {
    const value = { ...workspace.preferences, ...command.preferences }
    requireCondition(value.locale.trim() && value.fontId.trim(), 'validation.invalidPreferences')
    requireCondition(Number.isSafeInteger(value.themeId) && value.themeId >= 0, 'validation.invalidPreferences')
    requireCondition(Number.isInteger(value.weekStartsOn) && value.weekStartsOn >= 0 && value.weekStartsOn <= 6, 'validation.invalidPreferences')
    try { new Intl.DateTimeFormat(value.locale, { timeZone: value.timeZone }).format() } catch {
      throw new DomainError('validation.invalidPreferences')
    }
    assertOptionalPreferences(value, 'validation.invalidPreferences')
    workspace.preferences = value
    result = {}
  }
  if (command.type === 'saveCategory') {
    const current = command.categoryId ? workspace.categories.find(item => item.id === command.categoryId) : undefined
    requireCondition(!command.categoryId || current, 'validation.categoryMissing')
    requireCondition(/^#[a-f0-9]{6}$/i.test(command.color), 'validation.invalidColor')
    requireCondition(Number.isFinite(command.difficulty) && command.difficulty >= 0, 'validation.invalidDifficulty')
    const value = { id: current?.id || context.id(), name: current && command.name === undefined ? current.name : requireTitle(command.name || ''), color: command.color, difficulty: command.difficulty, icon: command.icon || current?.icon || 'circle' }
    if (current) Object.assign(current, value, { labelKey: command.name === undefined ? current.labelKey : undefined })
    else workspace.categories.push(value)
    result = { entityId: value.id }
  }
  requireCondition(result !== undefined, 'validation.unknownCommand')
  const cleanResult = Object.fromEntries(Object.entries(result).filter(([, value]) => value !== undefined)) as OperationResult
  if (cleanResult.recordId) {
    const record = workspace.records.find(item => item.id === cleanResult.recordId)
    if (record && !record.operationId) record.operationId = envelope.operationId
  }
  workspace.receipts[envelope.operationId] = { fingerprint, result: cleanResult }
  if (extension) (workspace.extensionAudit ||= []).push({ id: context.id(), kind: extension.kind, packageId: extension.packageId, action: 'write', occurredAt: normalizedContext.now, capabilities: [extension.scope], detail: command.type })
  workspace.revision = original.revision + 1
  workspace.updatedAt = normalizedContext.now
  return { workspace, result: cleanResult }
}

