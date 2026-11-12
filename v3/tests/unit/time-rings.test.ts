import { describe, it, expect } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import { categoryDetails, ringLayout } from '../../src/domain/time-details'
import type { Workspace } from '../../src/domain/models'

const date = '2026-11-11'
function context(sequence: number) {
  return { now: '2026-11-11T12:00:00Z', id: () => 'id-' + sequence }
}
function withPlan(state: Workspace, items: Array<{ categoryId: string; minutes: number }>) {
  return execute(state, {
    operationId: 'plan',
    command: { type: 'saveTimePlan', name: '工作日', mode: 'allocation', items, makeDefault: true },
  }, context(1)).workspace
}
function withRecord(state: Workspace, categoryId: string, startAt: string, endAt: string) {
  return execute(state, {
    operationId: 'record-' + startAt,
    command: { type: 'recordAction', title: '记录', content: '进展', categoryId, startAt, endAt },
  }, context(2)).workspace
}

describe('category ring targets', () => {
  it('keeps planned but unstarted categories visible with a full white ring', () => {
    const state = withPlan(emptyWorkspace('3.2.0', '2026-11-11T00:00:00Z', 'UTC'), [
      { categoryId: 'work', minutes: 120 },
      { categoryId: 'study', minutes: 60 },
    ])
    const groups = categoryDetails(state, date)
    expect(groups.map(group => group.category.id)).toEqual(['work', 'study'])
    const study = groups.find(group => group.category.id === 'study')!
    expect(study.started).toBe(false)
    expect(study.segments).toEqual([])
    expect(study.total).toBe(0)
    expect(study.target).toBe(60)
    const layout = ringLayout(study)
    expect(layout.fill).toBe(0)
    expect(layout.remaining).toBe(60)
    expect(layout.segments).toEqual([])
  })

  it('scales the recorded arc against the planned requirement', () => {
    let state = withPlan(emptyWorkspace('3.2.0', '2026-11-11T00:00:00Z', 'UTC'), [{ categoryId: 'work', minutes: 120 }])
    state = withRecord(state, 'work', '2026-11-11T09:00:00Z', '2026-11-11T09:30:00Z')
    const work = categoryDetails(state, date).find(group => group.category.id === 'work')!
    expect(work.target).toBe(120)
    expect(work.total).toBe(30)
    expect(work.started).toBe(true)
    const layout = ringLayout(work)
    expect(layout.fill).toBe(0.25)
    expect(layout.segments[0]!.length).toBeCloseTo(25)
    expect(layout.remaining).toBe(90)
  })

  it('falls back to recorded total when the requirement is met or absent', () => {
    let state = withPlan(emptyWorkspace('3.2.0', '2026-11-11T00:00:00Z', 'UTC'), [{ categoryId: 'work', minutes: 30 }])
    state = withRecord(state, 'work', '2026-11-11T09:00:00Z', '2026-11-11T10:00:00Z')
    const met = categoryDetails(state, date).find(group => group.category.id === 'work')!
    expect(ringLayout(met)).toMatchObject({ fill: 1, remaining: 0 })
    const unplanned = withRecord(emptyWorkspace('3.2.0', '2026-11-11T00:00:00Z', 'UTC'), 'life', '2026-11-11T09:00:00Z', '2026-11-11T10:00:00Z')
    const life = categoryDetails(unplanned, date).find(group => group.category.id === 'life')!
    expect(life.target).toBe(0)
    expect(ringLayout(life).fill).toBe(1)
  })

  it('does not invent rings for categories outside the plan', () => {
    const state = withPlan(emptyWorkspace('3.2.0', '2026-11-11T00:00:00Z', 'UTC'), [{ categoryId: 'work', minutes: 120 }])
    expect(categoryDetails(state, date).map(group => group.category.id)).toEqual(['work'])
  })
})
