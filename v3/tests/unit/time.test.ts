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
  it.each([
    ['America/Santiago', '2026-09-06', '2026-09-06T04:00:00Z', '2026-09-07T03:00:00Z', '2026-09-05'],
    ['America/Havana', '2026-03-08', '2026-03-08T05:00:00Z', '2026-03-09T04:00:00Z', '2026-03-07'],
  ])('starts %s at its first existing local time on %s', (zone, date, start, end, previous) => {
    expect(dayBounds(date!, zone!)).toEqual([Date.parse(start!), Date.parse(end!)])
    expect(dayBounds(previous!, zone!)[1]).toBe(Date.parse(start!))
    expect(recordedMinutes([record(start!, end!)], date!, zone!)).toBe(23 * 60)
  })
  it('uses the first midnight when midnight occurs twice', () => {
    expect(dayBounds('2026-11-01', 'America/Havana')).toEqual([Date.parse('2026-11-01T04:00:00Z'), Date.parse('2026-11-02T05:00:00Z')])
  })
  it('ends the prior day at a skipped calendar date boundary without inventing that day', () => {
    expect(dayBounds('2011-12-29', 'Pacific/Apia')).toEqual([Date.parse('2011-12-29T10:00:00Z'), Date.parse('2011-12-30T10:00:00Z')])
    expect(() => dayBounds('2011-12-30', 'Pacific/Apia')).toThrow('validation.invalidDate')
  })
  it('rejects invalid times and reversed intervals', () => {
    expect(() => minutesBetween('wrong', '2026-11-11T01:00:00Z')).toThrow('validation.invalidTime')
    expect(() => minutesBetween('2026-11-11T02:00:00Z', '2026-11-11T01:00:00Z')).toThrow('validation.timeOrder')
  })
  it('does not manufacture references without a previous observation', () => {
    expect(referenceFor(emptyWorkspace('3.0.0'), '2026-11-11T01:00:00Z')).toBeUndefined()
  })
})

