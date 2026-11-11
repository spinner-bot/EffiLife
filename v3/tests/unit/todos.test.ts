import { expect, it } from 'vitest'
import { emptyWorkspace } from '../../src/domain/initial'
import { execute } from '../../src/domain/engine'
import { assertWorkspace } from '../../src/domain/validation'
import { nextTodoOccurrence } from '../../src/domain/todo-recurrence'
import type { WorkspaceCommand } from '../../src/domain/commands'
import type { Todo } from '../../src/domain/models'

function setup(now = '2026-11-11T02:00:00Z', zone = 'Asia/Shanghai') {
  let workspace = emptyWorkspace('3.0.0', now, zone), id = 0, operation = 0
  return {
    get state() { return workspace },
    run(command: WorkspaceCommand, at = now) {
      const outcome = execute(workspace, { command, operationId: 'test-' + ++operation }, { now: at, id: () => 'id-' + ++id })
      assertWorkspace(outcome.workspace); workspace = outcome.workspace
      return outcome.result
    },
  }
}
function todo(at: string, frequency: 'day' | 'week' | 'month' = 'day'): Todo {
  return { id: 'one', title: 'Repeated', description: '', categoryId: 'life', createdAt: at, updatedAt: at, startAt: at, deadline: at, priorityRank: 5, important: false, urgent: false, estimatedMinutes: 0, status: 'pending', tags: [], recordIds: [], recurrence: { frequency, interval: 1 } }
}
it('keeps checklist progress independent of its parent completion and preserves timestamp provenance', () => {
  const f = setup()
  const id = f.run({ type: 'saveTodo', title: 'Shopping', pinned: true, subtasks: [{ id: 'salt', title: 'Salt', completed: false }, { id: 'bread', title: 'Bread', completed: false }] }).entityId!
  f.run({ type: 'setTodoSubtask', todoId: id, subtaskId: 'salt', completed: true })
  expect(f.state.todos[0]).toMatchObject({ status: 'pending', pinned: true, subtasks: [{ id: 'salt', completed: true, completedAt: '2026-11-11T02:00:00.000Z' }, { id: 'bread', completed: false }] })
  f.run({ type: 'setTodoPinned', todoId: id, pinned: false })
  expect(f.state.todos[0]?.pinned).toBe(false)
  expect(() => f.run({ type: 'saveTodo', todoId: id, title: 'Shopping', subtasks: [{ id: 'same', title: 'One', completed: false }, { id: 'same', title: 'Two', completed: true }] })).toThrow('validation.invalidSubtasks')
})
it('retains a completed occurrence and creates exactly one next pending checklist', () => {
  const f = setup()
  const id = f.run({ type: 'saveTodo', title: 'Review', deadline: '2026-11-11T09:00:00+08:00', recurrence: { frequency: 'day', interval: 1 }, subtasks: [{ id: 'chapter', title: 'Read chapter', completed: true }] }).entityId!
  f.run({ type: 'setTodoStatus', todoId: id, status: 'completed' })
  f.run({ type: 'setTodoStatus', todoId: id, status: 'completed' })
  f.run({ type: 'setTodoStatus', todoId: id, status: 'pending' })
  f.run({ type: 'setTodoStatus', todoId: id, status: 'completed' })
  expect(f.state.todos).toHaveLength(2)
  expect(f.state.todos[0]?.status).toBe('completed')
  expect(f.state.todos[1]).toMatchObject({ status: 'pending', previousOccurrenceId: id, deadline: '2026-11-12T01:00:00.000Z', subtasks: [{ completed: false }], recordIds: [] })
  expect(f.state.todos[0]?.nextOccurrenceId).toBe(f.state.todos[1]?.id)
  f.run({ type: 'deleteTodo', todoId: id })
  expect(f.state.todos[0]?.previousOccurrenceId).toBeUndefined()
})
it('preserves month-end intent through February', () => {
  const first = todo('2026-01-31T01:00:00Z', 'month')
  const february = nextTodoOccurrence(first, '2026-01-31T02:00:00Z', 'Asia/Shanghai')!
  expect(february.at).toBe('2026-02-28T01:00:00.000Z')
  expect(february.recurrence.anchorDay).toBe(31)
  expect(nextTodoOccurrence({ ...first, deadline: february.at, recurrence: february.recurrence }, '2026-02-28T02:00:00Z', 'Asia/Shanghai')?.at).toBe('2026-03-31T01:00:00.000Z')
})
it('schedules one future occurrence instead of generating every missed day', () => {
  expect(nextTodoOccurrence(todo('2026-11-01T01:00:00Z'), '2026-11-11T02:00:00Z', 'Asia/Shanghai')?.at).toBe('2026-11-12T01:00:00.000Z')
})
it('uses the first valid minute for a clock removed by a DST transition', () => {
  expect(nextTodoOccurrence(todo('2026-03-07T07:30:00Z'), '2026-03-07T08:00:00Z', 'America/New_York')?.at).toBe('2026-03-08T07:00:00.000Z')
  expect(nextTodoOccurrence(todo('2026-03-01T14:00:00Z', 'week'), '2026-03-01T15:00:00Z', 'America/New_York')?.at).toBe('2026-03-08T13:00:00.000Z')
})
it('preserves omitted deadline edits and accepts explicit clearing or recurrence removal', () => {
  const f = setup(), id = f.run({ type: 'saveTodo', title: 'One', deadline: '2026-12-01T00:00:00Z', recurrence: { frequency: 'week', interval: 2 } }).entityId!
  f.run({ type: 'saveTodo', todoId: id, title: 'Renamed' })
  expect(f.state.todos[0]?.deadline).toBe('2026-12-01T00:00:00.000Z')
  f.run({ type: 'saveTodo', todoId: id, title: 'Renamed', deadline: null, recurrence: null })
  expect(f.state.todos[0]?.deadline).toBeUndefined()
  expect(f.state.todos[0]?.recurrence).toBeUndefined()
})

