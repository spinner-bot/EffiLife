import type { TimeRecord, TimingReference, Workspace } from './models'
import { requireCondition } from './errors'

export function instant(value: string): string {
  const milliseconds = Date.parse(value)
  requireCondition(Number.isFinite(milliseconds), 'validation.invalidTime')
  return new Date(milliseconds).toISOString()
}

export function minutesBetween(startAt: string, endAt: string): number {
  const start = Date.parse(instant(startAt))
  const end = Date.parse(instant(endAt))
  requireCondition(end > start, 'validation.timeOrder')
  return (end - start) / 60000
}

export function dateKey(value: string | Date, timeZone: string): string {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(typeof value === 'string' ? new Date(value) : value)
  const field = (name: string) => parts.find(part => part.type === name)!.value
  return field('year') + '-' + field('month') + '-' + field('day')
}

function midnight(date: string, timeZone: string, allowSkippedDate = false): number {
  requireCondition(/^\d{4}-\d{2}-\d{2}$/.test(date), 'validation.invalidDate')
  const desired = Date.parse(date + 'T00:00:00Z')
  requireCondition(Number.isFinite(desired) && new Date(desired).toISOString().slice(0, 10) === date, 'validation.invalidDate')
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  })
  const localAsUTC = (candidate: number) => {
    const parts = formatter.formatToParts(new Date(candidate))
    const field = (name: string) => Number(parts.find(part => part.type === name)!.value)
    return Date.parse(String(field('year')).padStart(4, '0') + '-' + String(field('month')).padStart(2, '0') + '-' + String(field('day')).padStart(2, '0') + 'T' + [field('hour'), field('minute'), field('second')].map(value => String(value).padStart(2, '0')).join(':') + 'Z')
  }
  // Probe both sides of transitions instead of oscillating across a missing
  // midnight. Multiple exact matches are a fold: the day starts at the first.
  const candidates = new Set<number>()
  for (let hour = -48; hour <= 48; hour += 6) {
    const probe = desired + hour * 3600000
    candidates.add(desired - (localAsUTC(probe) - probe))
  }
  const exact = [...candidates].filter(value => localAsUTC(value) === desired)
  if (exact.length) return Math.min(...exact)
  // Missing midnight: find the transition itself, including gaps that start
  // on the previous evening. Never shift the requested day into the past.
  let before = Math.min(...candidates) - 1000
  let after = Math.max(...candidates)
  requireCondition(localAsUTC(before) < desired && localAsUTC(after) >= desired, 'validation.invalidDate')
  while (after - before > 1000) {
    const middle = Math.floor((before + after) / 2000) * 1000
    if (localAsUTC(middle) < desired) before = middle
    else after = middle
  }
  const candidate = after
  requireCondition(allowSkippedDate || dateKey(new Date(candidate), timeZone) === date, 'validation.invalidDate')
  return candidate
}

export function dayBounds(date: string, timeZone: string): [number, number] {
  const next = new Date(date + 'T12:00:00.000Z')
  requireCondition(Number.isFinite(next.getTime()), 'validation.invalidDate')
  next.setUTCDate(next.getUTCDate() + 1)
  return [midnight(date, timeZone), midnight(next.toISOString().slice(0, 10), timeZone, true)]
}

export function intervalsForDate(records: TimeRecord[], date: string, timeZone: string): Array<[number, number]> {
  const [start, end] = dayBounds(date, timeZone)
  return records.map(record => [Math.max(start, Date.parse(record.startAt)), Math.min(end, Date.parse(record.endAt))] as [number, number])
    .filter(([from, until]) => until > from)
}

export function unionMinutes(intervals: Array<[number, number]>): number {
  const sorted = [...intervals].sort((left, right) => left[0] - right[0])
  let end = -Infinity
  let total = 0
  for (const [from, until] of sorted) {
    if (until <= from) continue
    total += Math.max(0, until - Math.max(from, end))
    end = Math.max(end, until)
  }
  return total / 60000
}

export function recordedMinutes(records: TimeRecord[], date: string, timeZone: string): number {
  return unionMinutes(intervalsForDate(records, date, timeZone))
}

export function referenceFor(workspace: Workspace, occurredAt: string): TimingReference | undefined {
  const until = Date.parse(instant(occurredAt))
  const observations = [
    ...workspace.records.map(record => ({ id: record.id, at: record.endAt })),
    ...workspace.plans.flatMap(plan => plan.logs.filter(log => !log.timePrecision || log.timePrecision === 'minute').map(log => ({ id: log.id, at: log.occurredAt }))),
  ].filter(item => Number.isFinite(Date.parse(item.at)) && Date.parse(item.at) < until)
    .sort((left, right) => Date.parse(right.at) - Date.parse(left.at))
  const anchor = observations[0]
  if (!anchor) return undefined
  return {
    startAt: anchor.at, endAt: new Date(until).toISOString(),
    minutes: (until - Date.parse(anchor.at)) / 60000,
    source: 'previous-observation', anchorId: anchor.id,
  }
}

export function overlapMinutes(records: TimeRecord[], date: string, timeZone: string): number {
  const intervals = intervalsForDate(records, date, timeZone)
  return intervals.reduce((sum, [from, until]) => sum + (until - from) / 60000, 0) - unionMinutes(intervals)
}

export function zonedInstant(value: string, timeZone: string): string {
  requireCondition(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?$/.test(value), 'validation.invalidTime')
  const desired = Date.parse(value + 'Z')
  requireCondition(Number.isFinite(desired), 'validation.invalidTime')
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23',
  })
  const localAsUTC = (candidate: number) => {
    const parts = formatter.formatToParts(new Date(candidate))
    const field = (name: string) => Number(parts.find(part => part.type === name)!.value)
    return Date.UTC(field('year'), field('month') - 1, field('day'), field('hour'), field('minute'), field('second'))
  }
  let candidate = desired
  for (let iteration = 0; iteration < 4; iteration++) {
    const adjusted = desired - (localAsUTC(candidate) - candidate)
    if (candidate === adjusted) break
    candidate = adjusted
  }
  requireCondition(localAsUTC(candidate) === desired && new Date(desired).toISOString().slice(0, 16) === value.slice(0, 16), 'validation.invalidTime')
  return new Date(candidate).toISOString()
}

