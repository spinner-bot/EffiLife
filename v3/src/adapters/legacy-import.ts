import type { Workspace } from '../domain/models'
import { emptyWorkspace } from '../domain/initial'
import { assertWorkspace } from '../domain/validation'
import { importLegacyPlans } from './legacy-plans'
import { list, object, string, number, localInstant } from './legacy-utils'

export function importLegacy(
  source: unknown, version: string, timeZone: string, now = new Date().toISOString(),
): { workspace: Workspace; warnings: string[] } {
  const root = object(source)
  const app = object(root.app || root)
  const state = emptyWorkspace(version, now, timeZone)
  state.legacy = { importedAt: now, source: structuredClone(source) }
  const warnings: string[] = []
  if (typeof app.locale === 'string') {
    try { new Intl.DateTimeFormat(app.locale).format(); state.preferences.locale = app.locale } catch { warnings.push('legacy.localeInvalid') }
  }
  const categories = new Map<string, string>()
  let sequence = 0
  function category(name: string, oldId?: string, color?: string, difficulty = 5): string {
    const key = oldId || name || 'life'
    const known = categories.get(key)
    if (known) return known
    const id = 'legacy-category-' + ++sequence
    state.categories.push({ id, name: name || key, color: /^#[a-f0-9]{6}$/i.test(color || '') ? color! : '#526ac9', difficulty: Math.max(0, difficulty), icon: 'circle' })
    categories.set(key, id)
    if (name) categories.set(name, id)
    return id
  }
  for (const item of list(root.todo_categories || root.categories || app.categories)) {
    const value = object(item)
    category(string(value.name), String(value.id || ''), string(value.color), number(value.difficulty, 5))
  }
  const helper = object(root.plan_helper || root.planHelper || app.planHelper)
  const plans = Array.isArray(root.main) && root.head ? [root] : list(helper.plans || root.plans)
  const planMapping = importLegacyPlans(state, plans, warnings)
  for (const archivedValue of list(helper.archives)) {
    const archived = object(archivedValue)
    const payload = object(archived.payload)
    const archivedPlan = object(payload.plan || archived.plan)
    const marker = state.plans.length
    importLegacyPlans(state, Array.isArray(archivedPlan.main) ? [archivedPlan] : [], warnings)
    for (const plan of state.plans.slice(marker)) {
      if (state.plans.slice(0, marker).some(other => other.id === plan.id)) plan.id += '-archive-' + marker
      plan.archivedAt = string(payload.archived_at, now)
    }
  }
  const recordIds = new Map<string, string>()
  const records = object(root.records || root.time_records || app.records)
  for (const [date, values] of Object.entries(records)) for (const [index, item] of list(values).entries()) {
    const row = object(item)
    try {
      const startAt = localInstant(date, string(row.start || row['开始']), timeZone)
      let endAt = localInstant(date, string(row.end || row['结束']), timeZone)
      if (Date.parse(endAt) < Date.parse(startAt)) endAt = new Date(Date.parse(endAt) + 86400000).toISOString()
      if (Date.parse(endAt) <= Date.parse(startAt)) { warnings.push('legacy.recordTimeMissing'); continue }
      const id = 'legacy-record-' + date + '-' + index
      state.records.push({
        id, title: string(row.content || row['内容'], 'Activity'), note: '',
        categoryId: category(string(row.tag || row['标签'], 'life')), startAt, endAt,
        timing: 'actual', source: 'legacy-import',
      })
      if (row.id !== undefined) recordIds.set(String(row.id), id)
    } catch { warnings.push('legacy.recordInvalid') }
  }
  for (const [index, item] of list(root.todos || app.todos).entries()) {
    const row = object(item)
    const createdAt = string(row.created_at, now)
    if (!Number.isFinite(Date.parse(createdAt))) { warnings.push('legacy.todoInvalid'); continue }
    const rawStatus = string(row.status)
    const id = 'legacy-todo-' + String(row.id ?? index)
    if (state.todos.some(todo => todo.id === id)) { warnings.push('legacy.todoDuplicate'); continue }
    const links = list(row.related_time_record_ids).map(id => recordIds.get(String(id))).filter((id): id is string => Boolean(id))
    state.todos.push({
      id, title: string(row.title, 'Todo'), description: string(row.description || row.notes),
      categoryId: categories.get(string(row.category)) || category(string(row.category, 'life')),
      createdAt, updatedAt: string(row.updated_at, createdAt), startAt: string(row.start_time, createdAt),
      deadline: typeof row.deadline === 'string' && Number.isFinite(Date.parse(row.deadline)) ? row.deadline : undefined,
      priorityRank: Math.max(0, Math.trunc(number(row.priority_rank, 5))),
      urgent: Boolean(row.urgent), important: Boolean(row.important),
      estimatedMinutes: Math.max(0, number(row.estimated_time ?? row.time_estimate)),
      status: rawStatus === 'completed' ? 'completed' : ['archived', 'cancelled'].includes(rawStatus) ? 'archived' : 'pending',
      completedAt: typeof row.completed_at === 'string' && Number.isFinite(Date.parse(row.completed_at)) ? row.completed_at : undefined,
      tags: list(row.tags).filter((tag): tag is string => typeof tag === 'string'), recordIds: links,
    })
    const relatedPlan = planMapping.get(String(row.related_plan_id))
    const relatedTask = relatedPlan?.tasks.get(string(row.related_plan_task_id))
    if (relatedPlan && relatedTask) for (const recordId of links) {
      const record = state.records.find(record => record.id === recordId)!
      record.planId = relatedPlan.planId
      record.taskId = relatedTask
    }
  }
  if (Object.keys(app).length) warnings.push('legacy.originalPreserved')
  assertWorkspace(state)
  return { workspace: state, warnings: [...new Set(warnings)] }
}

