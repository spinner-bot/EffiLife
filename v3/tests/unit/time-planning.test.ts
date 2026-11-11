import { describe, expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import type { WorkspaceCommand } from '../../src/domain/commands'
import { resolveTimePlan, timePlanSummary, validRule } from '../../src/domain/time-planning'
import { importLegacy } from '../../src/adapters/legacy-import'

function setup() {
  let state = emptyWorkspace('3.0.0', '2026-11-11T00:00:00Z', 'Asia/Shanghai')
  let sequence = 0
  const run = (command: WorkspaceCommand) => {
    const result = execute(state, { operationId: 'operation-' + ++sequence, command }, { now: '2026-11-11T04:00:00Z', id: () => 'id-' + ++sequence })
    state = result.workspace
    return result.result.entityId!
  }
  const create = (name: string, mode: 'allocation' | 'partition' = 'allocation') => run({ type: 'saveTimePlan', name, mode, items: [{ categoryId: 'work', minutes: 480 }, { categoryId: 'rest', minutes: 480 }, { categoryId: 'life', minutes: 480 }], backgroundCategoryId: 'life' })
  return { state: () => state, run, create }
}

describe('daily time planning', () => {
  it('keeps a true zero baseline for allocation mode', () => {
    const f = setup()
    const id = f.create('Workday')
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: id })
    expect(timePlanSummary(f.state(), '2026-11-11', '2026-11-11T04:00:00Z')).toMatchObject({ background: 0, progress: 0 })
    expect(f.state().records).toHaveLength(0)
  })
  it('derives elapsed background for partition mode without creating actual records', () => {
    const f = setup()
    const id = f.create('Partition', 'partition')
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: id })
    const summary = timePlanSummary(f.state(), '2026-11-11', '2026-11-11T04:00:00Z')!
    expect(summary.background).toBe(720)
    expect(summary.progress).toBeCloseTo(100 / 3)
    expect(f.state().records).toHaveLength(0)
  })
  it('subtracts actual interval union from derived background', () => {
    const f = setup()
    const id = f.create('Partition', 'partition')
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: id })
    f.run({ type: 'recordAction', content: 'Work', categoryId: 'work', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T02:00:00Z' })
    expect(timePlanSummary(f.state(), '2026-11-11', '2026-11-11T04:00:00Z')!.background).toBe(660)
  })
  it('honors daily overrides, calendar rules and default precedence', () => {
    const f = setup()
    const a = f.create('Ordinary')
    const b = f.create('Wednesday')
    f.run({ type: 'saveTimeRule', kind: 'default', value: '', timePlanId: a })
    f.run({ type: 'saveTimeRule', kind: 'week', value: '3', timePlanId: b })
    expect(resolveTimePlan(f.state(), '2026-11-11')!.id).toBe(b)
    expect(resolveTimePlan(f.state(), '2026-11-12')!.id).toBe(a)
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: a })
    expect(resolveTimePlan(f.state(), '2026-11-11')!.id).toBe(a)
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: null })
    expect(resolveTimePlan(f.state(), '2026-11-11')!.id).toBe(b)
  })
  it('saves a template, default and selected date as one revision', () => {
    const f = setup()
    const id = f.run({ type: 'saveTimePlan', name: 'Daily', mode: 'allocation', items: [{ categoryId: 'work', minutes: 60 }], useForDate: '2026-11-11', makeDefault: true })
    expect(f.state().revision).toBe(1)
    expect(resolveTimePlan(f.state(), '2026-11-11')!.id).toBe(id)
    expect(resolveTimePlan(f.state(), '2026-11-12')!.id).toBe(id)
  })
  it('rejects invalid rules and cleans references when a template is deleted', () => {
    const f = setup()
    const id = f.create('Daily')
    expect(() => f.run({ type: 'saveTimeRule', kind: 'week', value: '8', timePlanId: id })).toThrow('validation.ruleInvalid')
    f.run({ type: 'saveTimeRule', kind: 'default', value: '', timePlanId: id })
    f.run({ type: 'setDateTimePlan', date: '2026-11-11', timePlanId: id })
    f.run({ type: 'deleteTimePlan', timePlanId: id })
    expect(f.state().timePlanning).toEqual({ plans: [], rules: [], overrides: {} })
    expect(validRule('year', '02-29,12-25')).toBe(true)
    expect(validRule('year', '02-31')).toBe(false)
    expect(validRule('month_week', '5-7')).toBe(true)
  })
  it('migrates legacy daily modes, hours, schedules and manual assignments', () => {
    const source = { records: {}, plans: { Workday: { plan_type: '切分制', items: [{ name: 'Work', hours: 8 }, { name: 'Life', hours: 16 }], bg_tag: 'Life' } }, scheduleRules: [{ rule_type: 'week', value: '1-5', plan_name: 'Workday' }], manualPlans: { '2026-11-11': 'Workday' } }
    const result = importLegacy(source, '3.0.0', 'Asia/Shanghai', '2026-11-11T00:00:00Z')
    const plan = resolveTimePlan(result.workspace, '2026-11-11')!
    expect(plan.mode).toBe('partition')
    expect(plan.items.map(item => item.minutes)).toEqual([480, 960])
    expect(result.workspace.legacy!.source).toEqual(source)
    expect(result.workspace.timePlanning!.rules[0]!.value).toBe('1-5')
  })
})
