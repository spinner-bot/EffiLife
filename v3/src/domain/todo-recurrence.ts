import type { Todo, TodoRecurrence } from './models'
import { dateKey, zonedInstant } from './time'
import { requireCondition } from './errors'

export function assertRecurrence(value: TodoRecurrence): void {
  requireCondition(value && ['day', 'week', 'month'].includes(value.frequency) && Number.isSafeInteger(value.interval) && value.interval > 0, 'validation.invalidRecurrence')
  requireCondition(value.anchorDay === undefined || Number.isInteger(value.anchorDay) && value.anchorDay >= 1 && value.anchorDay <= 31, 'validation.invalidRecurrence')
}
function localClock(value: string, zone: string) {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: zone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(new Date(value))
  return parts.find(part => part.type === 'hour')!.value + ':' + parts.find(part => part.type === 'minute')!.value
}
function resolveLocal(date: string, clock: string, zone: string): string {
  // If a spring transition removes the local clock time, use the first valid
  // minute after it; never silently convert it to a different calendar date.
  const desired = Date.parse(date + 'T' + clock + ':00Z')
  for (let offset = 0; offset <= 180; offset++) {
    const local = new Date(desired + offset * 60000).toISOString().slice(0, 16)
    try { return zonedInstant(local, zone) } catch { /* Try the next local minute. */ }
  }
  requireCondition(false, 'validation.invalidRecurrence')
}
export function nextTodoOccurrence(todo: Todo, completedAt: string, timeZone: string) {
  const rule = todo.recurrence
  if (!rule) return undefined
  assertRecurrence(rule)
  const base = todo.deadline || todo.startAt
  const date = dateKey(base, timeZone), today = dateKey(completedAt, timeZone)
  const [year, month, day] = date.split('-').map(Number) as [number, number, number]
  const [nowYear, nowMonth] = today.split('-').map(Number) as [number, number]
  const clock = localClock(base, timeZone)
  const anchorDay = rule.anchorDay || day
  const stepDays = rule.interval * (rule.frequency === 'week' ? 7 : 1)
  let steps = rule.frequency === 'month'
    ? Math.max(1, Math.floor(((nowYear - year) * 12 + nowMonth - month) / rule.interval))
    : Math.max(1, Math.floor((Date.parse(today + 'T12:00:00Z') - Date.parse(date + 'T12:00:00Z')) / 86400000 / stepDays))
  for (let attempt = 0; attempt < 3; attempt++, steps++) {
    let target: Date
    if (rule.frequency === 'month') {
      const start = new Date(Date.UTC(year, month - 1 + steps * rule.interval, 1, 12))
      const last = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 1, 0, 12)).getUTCDate()
      target = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth(), Math.min(anchorDay, last), 12))
    } else target = new Date(Date.parse(date + 'T12:00:00Z') + steps * stepDays * 86400000)
    requireCondition(Number.isFinite(target.getTime()) && target.getUTCFullYear() <= 9999, 'validation.invalidRecurrence')
    const at = resolveLocal(target.toISOString().slice(0, 10), clock, timeZone)
    if (Date.parse(at) > Date.parse(completedAt)) return { at, recurrence: { ...rule, anchorDay: rule.frequency === 'month' ? anchorDay : undefined } }
  }
  requireCondition(false, 'validation.invalidRecurrence')
}

