import { describe, expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import type { Workspace } from '../../src/domain/models'
import type { WorkspaceCommand } from '../../src/domain/commands'
import { assertWorkspace } from '../../src/domain/validation'

function fixture() {
  let next = 0
  let state = emptyWorkspace('3.0.0', '2026-11-11T00:00:00Z', 'Asia/Shanghai')
  function run(command: WorkspaceCommand, now = '2026-11-11T01:00:00Z', operationId = 'op-' + ++next) {
    const outcome = execute(state, { operationId, command }, { now, id: () => 'id-' + ++next })
    state = outcome.workspace
    return outcome.result
  }
  const planId = run({ type: 'createPlan', title: 'Mathematics' }).entityId!
  const sectionId = run({ type: 'addNode', planId, parentId: null, kind: 'section', title: 'Calculus', categoryId: 'study' }).entityId!
  const taskA = run({ type: 'addNode', planId, parentId: sectionId, kind: 'task', title: 'Chapter A' }).entityId!
  const taskB = run({ type: 'addNode', planId, parentId: sectionId, kind: 'task', title: 'Chapter B' }).entityId!
  return { run, planId, sectionId, taskA, taskB, state: () => state }
}

describe('unified recording', () => {
  it('creates actual time and an unfinished progress log together', () => {
    const f = fixture()
    const result = f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'First three sections', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T01:40:00Z' })
    const state = f.state()
    expect(state.records).toHaveLength(1)
    expect(state.plans[0]!.logs).toHaveLength(1)
    expect(state.records[0]).toMatchObject({ categoryId: 'study', logId: result.logId })
    expect(state.plans[0]!.logs[0]).toMatchObject({ taskId: f.taskA, kind: 'progress', recordIds: [result.recordId] })
    expect(state.plans[0]!.nodes.find(node => node.id === f.taskA)!.completedAt).toBeUndefined()
  })

  it('preserves progress-only logs without inventing actual time', () => {
    const f = fixture()
    f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'An idea', occurredAt: '2026-11-11T01:30:00Z' })
    expect(f.state().records).toEqual([])
    expect(f.state().plans[0]!.logs).toHaveLength(1)
  })

  it('uses the latest observation across tasks for a reference, without counting a whole interleaved span', () => {
    const f = fixture()
    for (const [taskId, time] of [[f.taskA, '01:30'], [f.taskB, '02:00'], [f.taskA, '02:20']] as const) {
      f.run({ type: 'recordAction', planId: f.planId, taskId, content: 'Progress', occurredAt: '2026-11-11T' + time + ':00Z' })
    }
    const logs = f.state().plans[0]!.logs
    expect(logs[2]!.timingReference).toMatchObject({ minutes: 20, anchorId: logs[1]!.id })
    expect(f.state().records).toHaveLength(0)
    expect(f.state().plans[0]!.nodes.find(node => node.id === f.taskA)!.completedAt).toBeUndefined()
  })

  it('changes completion only when explicitly requested', () => {
    const f = fixture()
    f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'Finished', completeTask: true, occurredAt: '2026-11-11T02:20:00Z' })
    expect(f.state().plans[0]!.nodes.find(node => node.id === f.taskA)!.completedAt).toBe('2026-11-11T02:20:00.000Z')
    expect(f.state().plans[0]!.logs[0]!.kind).toBe('completion')
  })

  it('deduplicates a retry and rejects reuse for another action', () => {
    const f = fixture()
    const command = { type: 'recordAction', content: 'Lunch', categoryId: 'life', startAt: '2026-11-11T04:00:00Z', endAt: '2026-11-11T04:30:00Z' } as const
    const result = f.run(command, undefined, 'retry')
    expect(f.run(command, undefined, 'retry')).toEqual(result)
    expect(f.state().records).toHaveLength(1)
    expect(() => f.run({ ...command, content: 'Something else' }, undefined, 'retry')).toThrow('validation.operationConflict')
  })

  it('rolls back invalid linked input and cleans references on deletion', () => {
    const f = fixture()
    const before = structuredClone(f.state())
    expect(() => f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'Invalid', startAt: '2026-11-11T02:00:00Z', endAt: '2026-11-11T01:00:00Z' })).toThrow('validation.timeOrder')
    expect(f.state()).toEqual(before)
    const result = f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'Worked', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T02:00:00Z' })
    f.run({ type: 'deleteRecord', recordId: result.recordId! })
    expect(f.state().records).toHaveLength(0)
    expect(f.state().plans[0]!.logs[0]!.recordIds).toEqual([])
  })

  it('keeps the same action description consistent when editing either view', () => {
    const f = fixture()
    const result = f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'Original progress', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T01:40:00Z' })
    const record = f.state().records[0]!
    f.run({ type: 'updateRecord', recordId: result.recordId!, title: record.title, note: 'Clarified from time view', categoryId: record.categoryId, startAt: record.startAt, endAt: record.endAt })
    expect(f.state().plans[0]!.logs[0]!.content).toBe('Clarified from time view')
    f.run({ type: 'updateLog', planId: f.planId, logId: result.logId!, content: 'Clarified from plan view' })
    expect(f.state().records[0]!.note).toBe('Clarified from plan view')
  })
  it('removes an action and its linked actual time without implicitly reopening its task', () => {
    const f = fixture()
    const result = f.run({ type: 'recordAction', planId: f.planId, taskId: f.taskA, content: 'Completed', completeTask: true, startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T01:40:00Z' })
    f.run({ type: 'saveTodo', title: 'History link' })
    f.state().todos[0]!.recordIds = [result.recordId!]
    f.run({ type: 'deleteLog', planId: f.planId, logId: result.logId! })
    expect(f.state().plans[0]!.logs).toEqual([])
    expect(f.state().records).toEqual([])
    expect(f.state().todos[0]!.recordIds).toEqual([])
    expect(f.state().plans[0]!.nodes.find(node => node.id === f.taskA)?.completedAt).toBeDefined()
  })
  it('links actual time to an independent todo without creating plan progress or completing it implicitly', () => {
    const f = fixture(), id = f.run({ type: 'saveTodo', title: 'Collect parcel', categoryId: 'life' }).entityId!
    const result = f.run({ type: 'recordAction', todoId: id, content: 'Collected one parcel', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T01:20:00Z' })
    expect(f.state().records[0]).toMatchObject({ title: 'Collect parcel', todoId: id, categoryId: 'life' })
    expect(f.state().todos[0]).toMatchObject({ status: 'pending', recordIds: [result.recordId] })
    expect(f.state().plans[0]!.logs).toEqual([])
    expect(() => assertWorkspace(f.state())).not.toThrow()
    f.run({ type: 'deleteTodo', todoId: id })
    expect(f.state().records).toHaveLength(1)
    expect(f.state().records[0]?.todoId).toBeUndefined()
    expect(() => assertWorkspace(f.state())).not.toThrow()
  })
  it('backfills historical todo completion while creating only a future repeat occurrence', () => {
    const f = fixture(), id = f.run({ type: 'saveTodo', title: 'Daily errand', deadline: '2026-11-01T01:00:00Z', recurrence: { frequency: 'day', interval: 1 } }).entityId!
    f.run({ type: 'recordAction', todoId: id, completeTodo: true, content: 'Historical errand', startAt: '2026-11-01T00:40:00Z', endAt: '2026-11-01T01:00:00Z' })
    expect(f.state().todos[0]).toMatchObject({ status: 'completed', completedAt: '2026-11-01T01:00:00.000Z' })
    expect(f.state().todos[1]).toMatchObject({ status: 'pending', deadline: '2026-11-12T01:00:00.000Z', createdAt: '2026-11-11T01:00:00.000Z', recordIds: [] })
    expect(() => assertWorkspace(f.state())).not.toThrow()
    const before = structuredClone(f.state())
    f.run({ type: 'setTodoStatus', todoId: id, status: 'archived' })
    expect(() => f.run({ type: 'recordAction', todoId: id, content: 'Invalid', startAt: '2026-11-11T01:00:00Z', endAt: '2026-11-11T01:20:00Z' })).toThrow('validation.todoArchived')
    expect(f.state().records).toEqual(before.records)
  })
})

