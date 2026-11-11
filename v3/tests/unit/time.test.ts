import { describe, expect, it } from 'vitest'
import { dayBounds, dateKey, minutesBetween, overlapMinutes, recordedMinutes, referenceFor } from '../../src/domain/time'
import { emptyWorkspace } from '../../src/domain/initial'
import type { TimeRecord } from '../../src/domain/models'

function record(startAt: string, endAt: string, id = startAt): TimeRecord {
  return { id, title: 'Activity', note: '', categoryId: 'life', startAt, endAt, timing: 'actual', source: 'manual' }
}

describe('actual time accounting', () => {
  it('counts overlapping intervals once for the whole day', () => {
    const rows = [record('2026-11-11T01:00:00Z', '2026-11-11T02:00:00Z'), record('2026-11-11T01:30:00Z', '2026-11-11T02:30:00Z')]
    expect(recordedMinutes(rows, '2026-11-11', 'Asia/Shanghai')).toBe(90)
    expect(overlapMinutes(rows, '2026-11-11', 'Asia/Shanghai')).toBe(30)
  })
  it('splits a cross-midnight record in the selected timezone', () => {
    const rows = [record('2026-11-11T15:30:00Z', '2026-11-11T16:30:00Z')]
    expect(recordedMinutes(rows, '2026-11-11', 'Asia/Shanghai')).toBe(30)
    expect(recordedMinutes(rows, '2026-11-12', 'Asia/Shanghai')).toBe(30)
    expect(dateKey(rows[0]!.startAt, 'Asia/Shanghai')).toBe('2026-11-11')
  })
  it('uses actual daylight-saving day boundaries', () => {
    const [start, end] = dayBounds('2026-03-08', 'America/New_York')
    expect((end - start) / 3600000).toBe(23)
    const [fallStart, fallEnd] = dayBounds('2026-11-01', 'America/New_York')
    expect((fallEnd - fallStart) / 3600000).toBe(25)
  })
  it('handles the full day without records', () => {
    expect(recordedMinutes([], '2026-11-11', 'Asia/Shanghai')).toBe(0)
  })
  it('rejects invalid times and reversed intervals', () => {
    expect(() => minutesBetween('wrong', '2026-11-11T01:00:00Z')).toThrow('validation.invalidTime')
    expect(() => minutesBetween('2026-11-11T02:00:00Z', '2026-11-11T01:00:00Z')).toThrow('validation.timeOrder')
  })
  it('does not manufacture references without a previous observation', () => {
    expect(referenceFor(emptyWorkspace('3.0.0'), '2026-11-11T01:00:00Z')).toBeUndefined()
  })
})

