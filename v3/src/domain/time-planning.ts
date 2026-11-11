import type { Workspace, TimePlanning, TimeRule } from './models'
import { dayBounds, intervalsForDate, recordedMinutes, unionMinutes } from './time'

export function planningOf(workspace: Workspace): TimePlanning {
  return workspace.timePlanning || { plans: [], rules: [], overrides: {} }
}

function matchesRange(value: string, target: number): boolean {
  return value.split(',').some(part => {
    const [start, end = start] = part.trim().split('-').map(Number)
    return Number.isInteger(start) && Number.isInteger(end) && target >= start! && target <= end!
  })
}
export function matchesRule(rule: TimeRule, date: string): boolean {
  const day = new Date(date + 'T12:00:00Z')
  const weekday = day.getUTCDay() || 7
  switch (rule.kind) {
    case 'week': return matchesRange(rule.value, weekday)
    case 'month': return matchesRange(rule.value, day.getUTCMonth() + 1)
    case 'year': return rule.value.split(',').map(item => item.trim()).includes(date.slice(5))
    case 'month_week': return rule.value === Math.floor((day.getUTCDate() - 1) / 7 + 1) + '-' + weekday
    default: return false
  }
}
export function resolveTimePlan(workspace: Workspace, date: string) {
  const planning = planningOf(workspace)
  const override = planning.overrides[date]
  if (override) return planning.plans.find(plan => plan.id === override)
  const rule = planning.rules.find(item => item.kind !== 'default' && matchesRule(item, date)) || [...planning.rules].reverse().find(item => item.kind === 'default')
  return planning.plans.find(plan => plan.id === rule?.planId)
}

export function timePlanSummary(workspace: Workspace, date: string, now: string) {
  const plan = resolveTimePlan(workspace, date)
  if (!plan) return undefined
  const zone = workspace.preferences.timeZone
  const [start, end] = dayBounds(date, zone)
  const availableEnd = Math.max(start, Math.min(end, Date.parse(now)))
  const observed = intervalsForDate(workspace.records, date, zone).map(([from, until]) => [from, Math.min(until, availableEnd)] as [number, number]).filter(([from, until]) => until > from)
  const background = plan.mode === 'partition' ? Math.max(0, (availableEnd - start) / 60000 - unionMinutes(observed)) : 0
  const items = plan.items.map(item => {
    const actual = recordedMinutes(workspace.records.filter(record => record.categoryId === item.categoryId), date, zone)
    const derived = item.categoryId === plan.backgroundCategoryId ? background : 0
    return { ...item, actual, derived, total: actual + derived }
  })
  const target = items.reduce((sum, item) => sum + item.minutes, 0)
  const contribution = Math.min(
    items.reduce((sum, item) => sum + Math.min(item.total, item.minutes), 0),
    recordedMinutes(workspace.records, date, zone) + background,
  )
  return { plan, items, target, background, progress: target > 0 ? contribution / target * 100 : 0 }
}
