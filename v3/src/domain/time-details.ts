import type { Category, TimeRecord, Workspace } from './models'
import { intervalsForDate, unionMinutes } from './time'
import { resolveTimePlan } from './time-planning'

export interface CategorySegment {
  record: TimeRecord
  minutes: number
  intervals: Array<[number, number]>
  color: string
  length: number
  offset: number
}

export interface CategoryDetail {
  category: Category
  total: number
  sum: number
  segments: CategorySegment[]
  overlap: number
  /** Planned minutes for the date; 0 when the category is not in the plan. */
  target: number
  /** False when the category was planned but has no records yet. */
  started: boolean
}

/** Record identity keeps its segment color when records are reordered or renamed. */
export function recordColor(id: string): string {
  let hash = 2166136261
  for (const char of id) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619)
  hash = Math.imul(hash ^ (hash >>> 16), 0x85ebca6b)
  hash = Math.imul(hash ^ (hash >>> 13), 0xc2b2ae35)
  const hue = ((hash ^ (hash >>> 16)) >>> 0) / 0x100000000 * 360
  return `hsl(${hue.toFixed(6)} 57% 53%)`
}

/** Planned minutes per category for the date, used as the ring's denominator. */
export function categoryTargets(workspace: Workspace, date: string): Map<string, number> {
  const plan = resolveTimePlan(workspace, date)
  return new Map(plan ? plan.items.map(item => [item.categoryId, item.minutes] as const) : [])
}

export function categoryDetails(workspace: Workspace, date: string): CategoryDetail[] {
  const targets = categoryTargets(workspace, date)
  return workspace.categories.flatMap((category): CategoryDetail[] => {
    const records = workspace.records.filter(record => record.categoryId === category.id).flatMap(record => {
      const intervals = intervalsForDate([record], date, workspace.preferences.timeZone)
      if (!intervals.length) return []
      return [{ record, minutes: unionMinutes(intervals), intervals, color: recordColor(record.id), length: 0, offset: 0 }]
    }).sort((a, b) => Date.parse(a.record.startAt) - Date.parse(b.record.startAt))
    const target = targets.get(category.id) ?? 0
    // A planned category still earns a ring before its first record, so the
    // remaining goal stays visible instead of the whole card disappearing.
    if (!records.length) return target > 0 ? [{ category, total: 0, sum: 0, segments: [], overlap: 0, target, started: false }] : []
    const sum = records.reduce((value, item) => value + item.minutes, 0)
    const total = unionMinutes(records.flatMap(item => item.intervals))
    let offset = 0
    const segments = records.map(item => {
      const length = item.minutes / sum * 100
      const value = { ...item, length, offset }; offset += length
      return value
    })
    return [{ category, total, sum, segments, overlap: sum - total, target, started: true }]
  })
}

/**
 * Scale segment arcs against the planned requirement. The full circle stands
 * for the target, so an unfinished day shows the gap instead of a full ring.
 */
export function ringLayout(group: CategoryDetail) {
  const denominator = Math.max(group.target, group.total, 1)
  const fill = group.total / denominator
  let offset = 0
  const segments = group.segments.map(segment => {
    const length = segment.length * fill
    const value = { ...segment, length, offset }
    offset += length
    return value
  })
  return { denominator, fill, segments, remaining: Math.max(0, group.target - group.total) }
}
