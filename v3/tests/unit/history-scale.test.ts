import { expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { assertWorkspace } from '../../src/domain/validation'

it('validates years of linked history and still rejects corruption at the tail', () => {
  const at = '2026-11-11T00:00:00Z'
  const state = emptyWorkspace('3.0.0', at, 'Asia/Shanghai')
  const ids = Array.from({ length: 15_000 }, (_, index) => 'record-' + index)
  state.records = ids.map((id, index) => ({ id, title: 'Action ' + index, note: '', categoryId: 'life', startAt: at, endAt: '2026-11-11T00:10:00Z', timing: 'actual', source: 'manual', planId: 'plan', logId: 'log-' + index, todoId: 'todo' }))
  state.plans = [{ id: 'plan', title: 'Long-running theme', description: '', createdAt: at, updatedAt: at, nodes: [], logs: ids.map((id, index) => ({ id: 'log-' + index, content: 'Progress', occurredAt: at, kind: 'progress', recordIds: [id] })) }]
  state.todos = [{ id: 'todo', title: 'Long-running item', description: '', categoryId: 'life', createdAt: at, updatedAt: at, startAt: at, urgent: false, important: false, priorityRank: 0, estimatedMinutes: 0, status: 'pending', tags: [], recordIds: [...ids] }]
  expect(() => assertWorkspace(state)).not.toThrow()
  state.plans[0]!.logs.at(-1)!.recordIds = ['missing-record']
  expect(() => assertWorkspace(state)).toThrow('storage.danglingReference')
  state.plans[0]!.logs.at(-1)!.recordIds = [ids.at(-1)!]
  state.records.at(-1)!.todoId = 'missing-todo'
  expect(() => assertWorkspace(state)).toThrow('storage.danglingReference')
}, 15_000)
