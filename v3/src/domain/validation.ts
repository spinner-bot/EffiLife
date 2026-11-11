import type { Workspace } from './models'
import { requireCondition } from './errors'
import { minutesBetween } from './time'
import { validRule } from './time-planning'
import type { TimeRule } from './models'

export function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value))
}
function rows(value: unknown): Array<Record<string, unknown>> {
  requireCondition(Array.isArray(value) && value.every(isObject), 'storage.invalidWorkspace')
  return value
}
function text(value: unknown): asserts value is string {
  requireCondition(typeof value === 'string', 'storage.invalidWorkspace')
}
function validInstant(value: unknown): asserts value is string {
  requireCondition(typeof value === 'string' && Number.isFinite(Date.parse(value)), 'storage.invalidWorkspace')
}
function unique(values: unknown[]) {
  requireCondition(values.every(value => typeof value === 'string' && value.length > 0) && new Set(values).size === values.length, 'storage.duplicateIdentity')
}

export function assertWorkspace(value: unknown): asserts value is Workspace {
  requireCondition(isObject(value) && value.schemaVersion === 1, 'storage.unsupportedSchema')
  text(value.productVersion)
  validInstant(value.updatedAt)
  requireCondition(Number.isSafeInteger(value.revision) && Number(value.revision) >= 0, 'storage.invalidWorkspace')
  const categories = rows(value.categories)
  unique(categories.map(category => category.id))
  const categoryIds = new Set(categories.map(category => category.id))
  for (const category of categories) {
    text(category.name); text(category.color); text(category.icon)
    requireCondition(Number.isFinite(category.difficulty) && Number(category.difficulty) >= 0, 'storage.invalidWorkspace')
  }
  const plans = rows(value.plans)
  unique(plans.map(plan => plan.id))
  const planNodes = new Map<string, Set<unknown>>()
  const logOwners = new Map<string, { planId: unknown; taskId: unknown; recordIds: unknown[] }>()
  for (const plan of plans) {
    text(plan.title); text(plan.description); validInstant(plan.createdAt); validInstant(plan.updatedAt)
    if (plan.archivedAt !== undefined) validInstant(plan.archivedAt)
    const nodes = rows(plan.nodes)
    unique(nodes.map(node => node.id))
    const byId = new Map(nodes.map(node => [node.id, node]))
    planNodes.set(String(plan.id), new Set(byId.keys()))
    for (const node of nodes) {
      text(node.title); text(node.description)
      requireCondition(['task', 'section', 'group'].includes(String(node.kind)), 'storage.invalidWorkspace')
      requireCondition(Number.isFinite(node.order) && Number.isFinite(node.estimatedMinutes) && Number(node.estimatedMinutes) >= 0, 'storage.invalidWorkspace')
      requireCondition(node.categoryId === undefined || categoryIds.has(node.categoryId), 'storage.danglingReference')
      if (node.completedAt !== undefined) validInstant(node.completedAt)
      const visited = new Set<unknown>([node.id])
      let parentId = node.parentId
      while (parentId !== null) {
        requireCondition(byId.has(parentId) && !visited.has(parentId), 'storage.invalidTree')
        visited.add(parentId)
        const parent = byId.get(parentId)!
        requireCondition(parent.kind !== 'task', 'storage.invalidTree')
        parentId = parent.parentId
      }
    }
    const logs = rows(plan.logs)
    unique(logs.map(log => log.id))
    for (const log of logs) {
      requireCondition(!logOwners.has(String(log.id)), 'storage.duplicateIdentity')
      text(log.content); validInstant(log.occurredAt)
      requireCondition(log.kind === 'progress' || log.kind === 'completion', 'storage.invalidWorkspace')
      requireCondition(log.taskId === undefined || byId.get(log.taskId)?.kind === 'task', 'storage.danglingReference')
      requireCondition(Array.isArray(log.recordIds), 'storage.invalidWorkspace')
      unique(log.recordIds)
      logOwners.set(String(log.id), { planId: plan.id, taskId: log.taskId, recordIds: log.recordIds })
    }
  }
  const records = rows(value.records)
  unique(records.map(record => record.id))
  for (const record of records) {
    text(record.title); text(record.note); validInstant(record.startAt); validInstant(record.endAt)
    minutesBetween(record.startAt, record.endAt)
    requireCondition(categoryIds.has(record.categoryId), 'storage.danglingReference')
    requireCondition(record.timing === 'actual' || record.timing === 'confirmed-reference', 'storage.invalidWorkspace')
    requireCondition(['manual', 'legacy-import', 'archive'].includes(String(record.source)), 'storage.invalidWorkspace')
    requireCondition(record.planId === undefined || planNodes.has(String(record.planId)), 'storage.danglingReference')
    requireCondition(record.taskId === undefined || planNodes.get(String(record.planId))?.has(record.taskId), 'storage.danglingReference')
    if (record.logId !== undefined) {
      const log = logOwners.get(String(record.logId))
      requireCondition(log && log.planId === record.planId && log.taskId === record.taskId && log.recordIds.includes(record.id), 'storage.danglingReference')
    }
  }
  const recordIds = new Set(records.map(record => record.id))
  for (const [id, log] of logOwners) for (const recordId of log.recordIds) {
    requireCondition(recordIds.has(recordId) && records.find(record => record.id === recordId)?.logId === id, 'storage.danglingReference')
  }
  const todos = rows(value.todos)
  unique(todos.map(todo => todo.id))
  for (const todo of todos) {
    text(todo.title); text(todo.description)
    validInstant(todo.createdAt); validInstant(todo.updatedAt); validInstant(todo.startAt)
    if (todo.deadline !== undefined) validInstant(todo.deadline)
    if (todo.completedAt !== undefined) validInstant(todo.completedAt)
    requireCondition(categoryIds.has(todo.categoryId), 'storage.danglingReference')
    requireCondition(['pending', 'completed', 'archived'].includes(String(todo.status)), 'storage.invalidWorkspace')
    requireCondition(typeof todo.urgent === 'boolean' && typeof todo.important === 'boolean', 'storage.invalidWorkspace')
    requireCondition(Number.isSafeInteger(todo.priorityRank) && Number(todo.priorityRank) >= 0 && Number.isFinite(todo.estimatedMinutes) && Number(todo.estimatedMinutes) >= 0, 'storage.invalidWorkspace')
    requireCondition(Array.isArray(todo.tags) && todo.tags.every(tag => typeof tag === 'string'), 'storage.invalidWorkspace')
    requireCondition(Array.isArray(todo.recordIds) && todo.recordIds.every(id => recordIds.has(id)), 'storage.danglingReference')
  }
  requireCondition(isObject(value.preferences), 'storage.invalidWorkspace')
  const preferences = value.preferences
  text(preferences.locale); text(preferences.fontId); text(preferences.timeZone)
  requireCondition(Number.isSafeInteger(preferences.themeId) && Number(preferences.themeId) >= 0, 'storage.invalidWorkspace')
  requireCondition(Number.isInteger(preferences.weekStartsOn) && Number(preferences.weekStartsOn) >= 0 && Number(preferences.weekStartsOn) <= 6, 'storage.invalidWorkspace')
  try { new Intl.DateTimeFormat(preferences.locale, { timeZone: preferences.timeZone }).format() } catch {
    requireCondition(false, 'storage.invalidWorkspace')
  }
  requireCondition(isObject(value.receipts), 'storage.invalidWorkspace')
  for (const receipt of Object.values(value.receipts)) requireCondition(isObject(receipt) && typeof receipt.fingerprint === 'string' && isObject(receipt.result), 'storage.invalidWorkspace')
  rows(value.packages)
  rows(value.packageTombstones)
  if (value.timePlanning !== undefined) {
    requireCondition(isObject(value.timePlanning), 'storage.invalidWorkspace')
    const planning = value.timePlanning
    const timePlans = rows(planning.plans)
    unique(timePlans.map(plan => plan.id))
    const ids = new Set(timePlans.map(plan => plan.id))
    for (const plan of timePlans) {
      text(plan.name)
      requireCondition(plan.mode === 'allocation' || plan.mode === 'partition', 'storage.invalidWorkspace')
      const items = rows(plan.items)
      unique(items.map(item => item.categoryId))
      requireCondition(items.length > 0, 'storage.invalidWorkspace')
      for (const item of items) requireCondition(categoryIds.has(item.categoryId) && Number.isFinite(item.minutes) && Number(item.minutes) >= 0, 'storage.invalidWorkspace')
      requireCondition(plan.mode !== 'partition' || items.some(item => item.categoryId === plan.backgroundCategoryId), 'storage.danglingReference')
    }
    const rules = rows(planning.rules)
    unique(rules.map(rule => rule.id))
    for (const rule of rules) requireCondition(typeof rule.value === 'string' && ids.has(rule.planId) && validRule(rule.kind as TimeRule['kind'], rule.value), 'storage.invalidWorkspace')
    requireCondition(isObject(planning.overrides), 'storage.invalidWorkspace')
    for (const [date, id] of Object.entries(planning.overrides)) requireCondition(/^\d{4}-\d{2}-\d{2}$/.test(date) && ids.has(id), 'storage.danglingReference')
  }
}

