import { describe, it, expect } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import { categoryDetails, recordColor } from '../../src/domain/time-details'
import { defaultHeaderClock } from '../../src/domain/preferences'
import { headerClockText } from '../../src/ui/header-clock'
import { assertWorkspace } from '../../src/domain/validation'

describe('daily category composition and clock preferences', () => {
  it('clips cross-day records, keeps unfinished work, and distinguishes union from composition', () => {
    let state = emptyWorkspace('3.1.0', '2026-11-11T00:00:00Z', 'UTC'), sequence = 0
    for (const [title, startAt, endAt] of [['Cross night', '2026-11-10T23:30:00Z', '2026-11-11T00:30:00Z'], ['Overlap', '2026-11-11T00:15:00Z', '2026-11-11T00:45:00Z']] as const) {
      state = execute(state, { operationId: 'op-' + ++sequence, command: { type: 'recordAction', title, content: 'Unfinished work', categoryId: 'study', startAt, endAt } }, { now: '2026-11-11T01:00:00Z', id: () => 'id-' + ++sequence }).workspace
    }
    const group = categoryDetails(state, '2026-11-11')[0]!
    expect(group.segments.map(segment => segment.minutes)).toEqual([30, 30])
    expect(group.sum).toBe(60); expect(group.total).toBe(45); expect(group.overlap).toBe(15)
    expect(group.segments.reduce((sum, segment) => sum + segment.length, 0)).toBeCloseTo(100)
    const color = group.segments[0]!.color
    state.records.reverse(); state.records[1]!.title = 'Renamed'
    expect(categoryDetails(state, '2026-11-11')[0]!.segments[0]!.color).toBe(color)
    expect(recordColor('one')).not.toBe(recordColor('two'))
    expect(categoryDetails(state, '2026-11-12')).toEqual([])
  })
  it('formats midnight as 00 in 24-hour mode and removes localized AM/PM when requested', () => {
    const now = '2026-11-11T16:05:00Z'
    expect(headerClockText(now, 'en-US', 'Asia/Shanghai', { ...defaultHeaderClock, display: 'time' })).toBe('00:05')
    expect(headerClockText(now, 'en-US', 'Asia/Shanghai', { ...defaultHeaderClock, display: 'time', hourCycle: 12 })).toMatch(/12:05.*AM/)
    expect(headerClockText(now, 'en-US', 'Asia/Shanghai', { ...defaultHeaderClock, display: 'time', hourCycle: 12, showPeriod: false })).toBe('12:05')
    expect(headerClockText(now, 'zh-CN', 'Asia/Shanghai', { ...defaultHeaderClock, display: 'both' })).toContain('11月12日')
  })
  it('accepts old preferences and rejects malformed optional clock settings in imports', () => {
    const state = emptyWorkspace('3.1.0')
    expect(() => assertWorkspace(state)).not.toThrow()
    Object.assign(state.preferences, { headerClock: { ...defaultHeaderClock, hourCycle: 13 } })
    expect(() => assertWorkspace(state)).toThrow('storage.invalidWorkspace')
    expect(() => execute(emptyWorkspace('3.1.0'), { operationId: 'invalid-clock', command: { type: 'savePreferences', preferences: state.preferences } }, { now: new Date().toISOString(), id: () => 'id' })).toThrow('validation.invalidPreferences')
  })
})
