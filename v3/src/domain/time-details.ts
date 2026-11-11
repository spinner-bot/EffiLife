import type { Workspace } from './models'
import { intervalsForDate, unionMinutes } from './time'

/** Record identity keeps its segment color when records are reordered or renamed. */
export function recordColor(id: string): string {
  let hash = 2166136261
  for (const char of id) hash = Math.imul(hash ^ char.charCodeAt(0), 16777619)
  hash = Math.imul(hash ^ (hash >>> 16), 0x85ebca6b)
  hash = Math.imul(hash ^ (hash >>> 13), 0xc2b2ae35)
  const hue = ((hash ^ (hash >>> 16)) >>> 0) / 0x100000000 * 360
  return `hsl(${hue.toFixed(6)} 57% 53%)`
}
export function categoryDetails(workspace: Workspace, date: string) {
  return workspace.categories.flatMap(category => {
    const records = workspace.records.filter(record => record.categoryId === category.id).flatMap(record => {
      const intervals = intervalsForDate([record], date, workspace.preferences.timeZone)
      if (!intervals.length) return []
      return [{ record, minutes: unionMinutes(intervals), intervals, color: recordColor(record.id) }]
    }).sort((a, b) => Date.parse(a.record.startAt) - Date.parse(b.record.startAt))
    if (!records.length) return []
    const sum = records.reduce((value, item) => value + item.minutes, 0)
    const total = unionMinutes(records.flatMap(item => item.intervals))
    let offset = 0
    const segments = records.map(item => {
      const length = item.minutes / sum * 100
      const value = { ...item, length, offset }; offset += length
      return value
    })
    return [{ category, total, sum, segments, overlap: sum - total }]
  })
}
