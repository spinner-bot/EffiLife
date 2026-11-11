import type { Workspace, TimeRule } from '../domain/models'
import { object, list, string, number } from './legacy-utils'
import { validRule } from '../domain/time-planning'

export function importLegacyTimePlanning(
  workspace: Workspace, app: Record<string, unknown>, category: (name: string) => string, warnings: string[],
) {
  const planning = workspace.timePlanning ||= { plans: [], rules: [], overrides: {} }
  const ids = new Map<string, string>()
  for (const [name, value] of Object.entries(object(app.plans))) {
    const raw = object(value)
    const items = list(raw.items).map(item => object(item)).filter(item => typeof item.name === 'string')
      .map(item => ({ categoryId: category(string(item.name)), minutes: Math.max(0, number(item.hours) * 60) }))
    if (!items.length) continue
    const backgroundName = string(raw.bg_tag)
    const backgroundCategoryId = backgroundName ? category(backgroundName) : undefined
    const mode = raw.plan_type === '切分制' || raw.type === '切分制' ? 'partition' : 'allocation'
    if (mode === 'partition' && !backgroundCategoryId) { warnings.push('legacy.timePlanInvalid'); continue }
    if (backgroundCategoryId && !items.some(item => item.categoryId === backgroundCategoryId)) items.push({ categoryId: backgroundCategoryId, minutes: 0 })
    const merged = new Map<string, number>()
    for (const item of items) merged.set(item.categoryId, (merged.get(item.categoryId) || 0) + item.minutes)
    const id = 'legacy-time-plan-' + planning.plans.length
    planning.plans.push({ id, name, mode, items: [...merged].map(([categoryId, minutes]) => ({ categoryId, minutes })), backgroundCategoryId })
    ids.set(name, id)
  }
  for (const value of list(app.scheduleRules || app.schedule_rules)) {
    const raw = object(value)
    const planId = ids.get(string(raw.plan_name))
    const kind = string(raw.rule_type) as TimeRule['kind']
    const expression = string(raw.value)
    if (!planId || !validRule(kind, expression)) { warnings.push('legacy.ruleInvalid'); continue }
    planning.rules.push({ id: 'legacy-rule-' + planning.rules.length, kind, value: expression, planId })
  }
  if (planning.plans.length && !planning.rules.some(rule => rule.kind === 'default')) planning.rules.push({ id: 'legacy-default-rule', kind: 'default', value: '', planId: planning.plans[0]!.id })
  for (const [date, name] of Object.entries(object(app.manualPlans || app.manual_plans))) {
    const planId = ids.get(String(name))
    if (planId && /^\d{4}-\d{2}-\d{2}$/.test(date)) planning.overrides[date] = planId
    else warnings.push('legacy.ruleInvalid')
  }
}
